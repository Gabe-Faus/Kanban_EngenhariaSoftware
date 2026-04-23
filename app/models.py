
class Usuario:
    def __init__(self, nome, email, senha, foto, id=None):
        self.id = id  # Set by database after insertion
        self.nome = nome
        self.email = email
        self.senha = senha
        self.foto = foto