from app.services.quadro_service import QuadroService
from app.db.connection import Database
from psycopg2 import Error
from datetime import datetime

VALID_ACESSO_TYPES = ("DONO", "EDITOR", "LEITOR")

def associar_usuario_quadro(id_usuario, id_quadro, tipo_acesso="LEITOR", data_associacao=None):
    if tipo_acesso not in VALID_ACESSO_TYPES:
        tipo_acesso = "LEITOR"

    if data_associacao is None:
        data_associacao = datetime.now()

    try:
        db = Database()
        query = """
            INSERT INTO USUARIO_QUADRO (ID_USUARIO, ID_QUADRO, DATA_ASSOCIACAO, TIPO_ACESSO)
            VALUES (%s, %s, %s, %s)
            RETURNING ID_USUARIO, ID_QUADRO
        """
        db.cursor.execute(query, (id_usuario, id_quadro, data_associacao, tipo_acesso))
        db.commit()

        result = db.cursor.fetchone()
        if result:
            id_usuario_db, id_quadro_db = result
            return {
                "id_usuario": id_usuario_db,
                "id_quadro": id_quadro_db,
                "tipo_acesso": tipo_acesso,
                "data_associacao": data_associacao
            }
        return None

    except Error as e:
        print(f"Error creating usuario_quadro: {e}")
        db.conn.rollback()
        return None


def criar_quadro_com_usuario(id_usuario, nome, descricao, data_criacao, tipo_acesso="DONO"):
    quadro = QuadroService().criar_quadro(nome, descricao, data_criacao)
    if not quadro:
        return None

    associacao = associar_usuario_quadro(id_usuario, quadro.id, tipo_acesso=tipo_acesso)
    if not associacao:
        return None

    return {
        "quadro": quadro,
        "associacao": associacao
    }