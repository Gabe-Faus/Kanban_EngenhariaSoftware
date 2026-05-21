from app.models import Usuario
from app.db.connection import Database
from psycopg2 import Error


class UsuarioService:
    def __init__(self):
        self.db = Database()

    def criar_usuario(self, nome, email, senha, foto=None):
        """
        Insert a new user into the database
        Returns: Usuario object with ID if successful, None if failed
        """
        try:
            query = """
                INSERT INTO USUARIO (NOME, EMAIL, SENHA, FOTO)
                VALUES (%s, %s, %s, %s)
                RETURNING ID_USUARIO, NOME, EMAIL, SENHA, FOTO
            """
            self.db.cursor.execute(query, (nome, email, senha, foto))
            self.db.commit()
            
            result = self.db.cursor.fetchone()
            if result:
                usuario_id, nome_db, email_db, senha_db, foto_db = result
                usuario = Usuario(nome_db, email_db, senha_db, foto_db, id=usuario_id)
                return usuario
            return None
            
        except Error as e:
            print(f"Error creating user: {e}")
            self.db.conn.rollback()
            return None

    def obter_usuario(self, id_usuario):
        """
        Get a user by ID
        Returns: Usuario object if found, None otherwise
        """
        try:
            query = "SELECT ID_USUARIO, NOME, EMAIL, SENHA, FOTO FROM USUARIO WHERE ID_USUARIO = %s"
            self.db.cursor.execute(query, (id_usuario,))
            
            result = self.db.cursor.fetchone()
            if result:
                usuario_id, nome, email, senha, foto = result
                return Usuario(nome, email, senha, foto, id=usuario_id)
            return None
            
        except Error as e:
            print(f"Error retrieving user: {e}")
            return None

    def obter_usuario_por_email(self, email):
        """
        Get a user by email
        Returns: Usuario object if found, None otherwise
        """
        try:
            query = "SELECT ID_USUARIO, NOME, EMAIL, FOTO FROM USUARIO WHERE EMAIL = %s"
            self.db.cursor.execute(query, (email,))
            
            result = self.db.cursor.fetchone()
            if result:
                usuario_id, nome, email_db, foto = result
                return Usuario(nome, email_db, foto, id=usuario_id)
            return None
            
        except Error as e:
            print(f"Error retrieving user by email: {e}")
            return None

    def listar_usuarios(self):
        """
        Get all users from the database
        Returns: List of Usuario objects
        """
        try:
            query = "SELECT ID_USUARIO, NOME, EMAIL, FOTO FROM USUARIO ORDER BY ID_USUARIO"
            self.db.cursor.execute(query)
            
            usuarios = []
            for row in self.db.cursor.fetchall():
                usuario_id, nome, email, foto = row
                usuarios.append(Usuario(nome, email, foto, id=usuario_id))
            
            return usuarios
            
        except Error as e:
            print(f"Error listing users: {e}")
            return []

    def atualizar_usuario(self, id_usuario, nome=None, email=None, senha=None, foto=None):
        """
        Update user information
        Returns: Updated Usuario object if successful, None if user not found or error
        """
        try:
            # Build dynamic query based on provided parameters
            updates = []
            params = []
            
            if nome is not None:
                updates.append("NOME = %s")
                params.append(nome)
            if email is not None:
                updates.append("EMAIL = %s")
                params.append(email)
            if senha is not None:
                updates.append("SENHA = %s")
                params.append(senha)
            if foto is not None:
                updates.append("FOTO = %s")
                params.append(foto)
            
            if not updates:
                # No updates provided
                return self.obter_usuario(id_usuario)
            
            # Add ID to params for WHERE clause
            params.append(id_usuario)
            
            query = f"""
                UPDATE USUARIO 
                SET {', '.join(updates)}
                WHERE ID_USUARIO = %s
                RETURNING ID_USUARIO, NOME, EMAIL, FOTO
            """
            
            self.db.cursor.execute(query, params)
            self.db.commit()
            
            result = self.db.cursor.fetchone()
            if result:
                usuario_id, nome_db, email_db, foto_db = result
                return Usuario(nome_db, email_db, foto_db, id=usuario_id)
            return None
            
        except Error as e:
            print(f"Error updating user: {e}")
            self.db.conn.rollback()
            return None

    def deletar_usuario(self, id_usuario):
        """
        Delete a user from the database
        Returns: True if successful, False otherwise
        """
        try:
            query = "DELETE FROM USUARIO WHERE ID_USUARIO = %s"
            self.db.cursor.execute(query, (id_usuario,))
            self.db.commit()
            
            # Check if any row was deleted
            if self.db.cursor.rowcount > 0:
                return True
            return False
            
        except Error as e:
            print(f"Error deleting user: {e}")
            self.db.conn.rollback()
            return False

    def fechar_conexao(self):
        """Close the database connection"""
        try:
            self.db.close()
        except Error as e:
            print(f"Error closing connection: {e}")