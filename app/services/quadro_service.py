from app.models import Quadro
from app.db.connection import Database
from psycopg2 import Error


class QuadroService:
    def __init__(self):
        self.db = Database()

    def criar_quadro(self, nome, descricao, data_criacao):
        """
        Insert a new quadro into the database
        Returns: Quadro object with ID if successful, None if failed
        """
        try:
            query = """
                INSERT INTO QUADRO (NOME, DESCRICAO, DATA_CRIACAO)
                VALUES (%s, %s, %s)
                RETURNING ID_QUADRO, NOME, DESCRICAO, DATA_CRIACAO
            """
            self.db.cursor.execute(query, (nome, descricao, data_criacao))
            self.db.commit()
            
            result = self.db.cursor.fetchone()
            if result:
                quadro_id, nome_db, descricao_db, data_criacao_db = result
                quadro = Quadro(nome_db, descricao_db, data_criacao_db, id=quadro_id)
                return quadro
            return None
            
        except Error as e:
            print(f"Error creating quadro: {e}")
            self.db.conn.rollback()
            return None
        
    def obter_quadro(self, id_quadro):
        """
        Get a quadro by ID
        Returns: Quadro object if found, None otherwise
        """
        try:
            query = "SELECT ID_QUADRO, NOME, DESCRICAO, DATA_CRIACAO FROM QUADRO WHERE ID_QUADRO = %s"
            self.db.cursor.execute(query, (id_quadro,))
            
            result = self.db.cursor.fetchone()
            if result:
                quadro_id, nome, descricao, data_criacao = result
                return Quadro(nome, descricao, data_criacao, id=quadro_id)
            return None
            
        except Error as e:
            print(f"Error retrieving quadro: {e}")
            return None
    
    def listar_quadros(self):
        try:
            query = "SELECT ID_QUADRO, NOME, DESCRICAO, DATA_CRIACAO FROM QUADRO ORDER BY ID_QUADRO"
            self.db.cursor.execute(query)
            quadros = []
            for row in self.db.cursor.fetchall():
                quadro_id, nome, descricao, data_criacao = row
                quadros.append(Quadro(nome, descricao, data_criacao, id=quadro_id))
            return quadros
        except Error as e:
            print(f"Error listing quadros: {e}")
            return []

    def listar_quadros_por_usuario(self, id_usuario):
        try:
            query = """
                SELECT q.ID_QUADRO, q.NOME, q.DESCRICAO, q.DATA_CRIACAO
                FROM QUADRO q
                JOIN USUARIO_QUADRO uq ON uq.ID_QUADRO = q.ID_QUADRO
                WHERE uq.ID_USUARIO = %s
                ORDER BY q.ID_QUADRO
            """
            self.db.cursor.execute(query, (id_usuario,))
            quadros = []
            for row in self.db.cursor.fetchall():
                quadro_id, nome, descricao, data_criacao = row
                quadros.append(Quadro(nome, descricao, data_criacao, id=quadro_id))
            return quadros
        except Error as e:
            print(f"Error listing quadros for user {id_usuario}: {e}")
            return []
        
    def deletar_quadro(self, id_quadro):
        """
        Delete a quadro by ID
        Returns: True if deleted successfully, False otherwise
        """
        try:
            query = "DELETE FROM QUADRO WHERE ID_QUADRO = %s"
            self.db.cursor.execute(query, (id_quadro,))
            self.db.commit()
            return self.db.cursor.rowcount > 0
            
        except Error as e:
            print(f"Error deleting quadro: {e}")
            self.db.conn.rollback()
            return False    
            
    