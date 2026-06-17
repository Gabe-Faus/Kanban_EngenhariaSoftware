from app.services.quadro_service import QuadroService
from app.services.usuarioquadro_service import criar_quadro_com_usuario
from app.db.connection import Database
from app.models import Raia
from psycopg2 import Error  
from datetime import datetime

class RaiaService:
    def criar_raia(qtd_max, nome, id_quadro, ordem=0):
        try:
            db = Database()
            query = """
                INSERT INTO RAIA (QTD_MAX, NOME, ID_QUADRO, ORDEM)
                VALUES (%s, %s, %s, %s)
                RETURNING ID_RAIA, QTD_MAX, NOME, ID_QUADRO
            """
            db.cursor.execute(query, (qtd_max, nome, id_quadro, ordem))
            db.commit()

            result = db.cursor.fetchone()
            if result:
                id_raia_db, qtd_max_db, nome_db, id_quadro_db = result
                return Raia(qtd_max_db, nome_db, id_quadro_db, id=id_raia_db)
            return None

        except Error as e:
            print(f"Error creating raia: {e}")
            db.conn.rollback()
            return None
        
    def deletar_raia(id_raia):
        try:
            db = Database()
            query = "DELETE FROM RAIA WHERE ID_RAIA = %s"
            db.cursor.execute(query, (id_raia,))
            db.commit()
            return db.cursor.rowcount > 0  # Returns True if a row was deleted
        except Error as e:
            print(f"Error deleting raia: {e}")
            db.conn.rollback()
            return False

    def obter_raia(id_raia):
        try:
            db = Database()
            query = "SELECT ID_RAIA, QTD_MAX, NOME, ID_QUADRO FROM RAIA WHERE ID_RAIA = %s"
            db.cursor.execute(query, (id_raia,))
            
            result = db.cursor.fetchone()
            if result:
                id_raia_db, qtd_max_db, nome_db, id_quadro_db = result
                return Raia(qtd_max_db, nome_db, id_quadro_db, id=id_raia_db)
            return None

        except Error as e:
            print(f"Error retrieving raia: {e}")
            return None

    def listar_raias_por_quadro(id_quadro):
        try:
            db = Database()
            query = "SELECT ID_RAIA, QTD_MAX, NOME, ID_QUADRO FROM RAIA WHERE ID_QUADRO = %s ORDER BY ORDEM, ID_RAIA"
            db.cursor.execute(query, (id_quadro,))

            raiais = []
            for row in db.cursor.fetchall():
                id_raia_db, qtd_max_db, nome_db, id_quadro_db = row
                raiais.append(Raia(qtd_max_db, nome_db, id_quadro_db, id=id_raia_db))

            return raiais

        except Error as e:
            print(f"Error listing raia for quadro {id_quadro}: {e}")
            return []

    def atualizar_raia(raia_id, nome=None):
        try:
            db = Database()
            if nome:
                db.cursor.execute("UPDATE RAIA SET NOME = %s WHERE ID_RAIA = %s", (nome.strip(), raia_id))
            db.commit()
            return True
        except Error as e:
            print(f"Error updating raia: {e}")
            db.conn.rollback()
            return False

    def contar_raias_por_quadro(id_quadro):
        try:
            db = Database()
            db.cursor.execute("SELECT COUNT(*) FROM RAIA WHERE ID_QUADRO = %s", (id_quadro,))
            return db.cursor.fetchone()[0]
        except Error as e:
            print(f"Error counting raias: {e}")
            return 0

    def obter_proxima_ordem(id_quadro):
        try:
            db = Database()
            db.cursor.execute("SELECT COALESCE(MAX(ORDEM), -1) + 1 FROM RAIA WHERE ID_QUADRO = %s", (id_quadro,))
            return db.cursor.fetchone()[0]
        except Error as e:
            print(f"Error getting next ordem: {e}")
            return 0
