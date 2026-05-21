from app.models import Cartao
from app.db.connection import Database  
from psycopg2 import Error

class CartaoService:
    def criar_cartao(data_incio, data_final, data_criacao, nome, ordem, id_raia, id_cor, descricao):
        try:
            db = Database()
            query = """
                INSERT INTO CARTAO (DATA_INICIO, DATA_FINAL, DATA_CRIACAO, NOME, ORDEM, ID_RAIA, ID_COR, DESCRICAO)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING ID_CARTAO, DATA_INICIO, DATA_FINAL, DATA_CRIACAO, NOME, ORDEM, ID_RAIA, ID_COR, DESCRICAO
            """
            db.cursor.execute(query, (data_incio, data_final, data_criacao, nome, ordem, id_raia, id_cor, descricao))
            db.commit()

            result = db.cursor.fetchone()
            if result:
                id_cartao_db, data_inicio_db, data_final_db, data_criacao_db, nome_db, ordem_db, id_raia_db, id_cor_db, descricao_db = result
                return Cartao(data_inicio_db, data_final_db, data_criacao_db,
                              nome_db, ordem_db,
                              id_raia_db,
                              id_cor_db,
                              descricao_db,
                              id=id_cartao_db)
            return None

        except Error as e:
            print(f"Error creating cartao: {e}")
            db.conn.rollback()
            return None
    
    def deletar_cartao(id_cartao):
        try:
            db = Database()
            query = "DELETE FROM CARTAO WHERE ID_CARTAO = %s"
            db.cursor.execute(query, (id_cartao,))
            db.commit()
            return db.cursor.rowcount > 0  # Returns True if a row was deleted
        except Error as e:
            print(f"Error deleting cartao: {e}")
            db.conn.rollback()
            return False
        
    def obter_cartao(id_cartao):
        try:
            db = Database()
            query = "SELECT ID_CARTAO, DATA_INICIO, DATA_FINAL, DATA_CRIACAO, NOME, ORDEM, ID_RAIA, ID_COR, DESCRICAO FROM CARTAO WHERE ID_CARTAO = %s"
            db.cursor.execute(query, (id_cartao,))
            
            result = db.cursor.fetchone()
            if result:
                id_cartao_db, data_inicio_db, data_final_db, data_criacao_db, nome_db, ordem_db, id_raia_db, id_cor_db, descricao_db = result
                return Cartao(data_inicio_db, data_final_db, data_criacao_db,
                              nome_db, ordem_db,
                              id_raia_db,
                              id_cor_db,
                              descricao_db,
                              id=id_cartao_db)
            return None

        except Error as e:
            print(f"Error retrieving cartao: {e}")
            return None

    def listar_cartoes_por_raia(id_raia):
        try:
            db = Database()
            query = "SELECT ID_CARTAO, DATA_INICIO, DATA_FINAL, DATA_CRIACAO, NOME, ORDEM, ID_RAIA, ID_COR, DESCRICAO FROM CARTAO WHERE ID_RAIA = %s ORDER BY ORDEM, ID_CARTAO"
            db.cursor.execute(query, (id_raia,))

            cartoes = []
            for row in db.cursor.fetchall():
                id_cartao_db, data_inicio_db, data_final_db, data_criacao_db, nome_db, ordem_db, id_raia_db, id_cor_db, descricao_db = row
                cartoes.append(Cartao(data_inicio_db, data_final_db, data_criacao_db,
                                       nome_db, ordem_db,
                                       id_raia_db,
                                       id_cor_db,
                                       descricao_db,
                                       id=id_cartao_db))

            return cartoes

        except Error as e:
            print(f"Error listing cartoes for raia {id_raia}: {e}")
            return []