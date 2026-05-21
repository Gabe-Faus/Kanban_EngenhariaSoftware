from app.services.raia_service import RaiaService
from app.services.usuario_service import UsuarioService
from app.services.cartao_service import CartaoService
from app.db.connection import Database
from psycopg2 import Error

class UsuarioCartaoService:
    def criar_usuario_cartao(id_usuario, id_cartao):
        try:
            db = Database()
            query = """
                INSERT INTO USUARIO_CARTAO (ID_USUARIO, ID_CARTAO)
                VALUES (%s, %s)
                RETURNING ID_USUARIO, ID_CARTAO
            """
            db.cursor.execute(query, (id_usuario, id_cartao))
            db.commit()

            result = db.cursor.fetchone()
            if result:
                id_usuario_db, id_cartao_db = result
                return {
                    "id_usuario": id_usuario_db,
                    "id_cartao": id_cartao_db
                }
            return None

        except Error as e:
            print(f"Error creating usuario_cartao: {e}")
            db.conn.rollback()
            return None
    
    