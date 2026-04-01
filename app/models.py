
class Usuario:
    def __init__(self, nome, email, foto, id=None):
        self.id = id  # Set by database after insertion
        self.nome = nome
        self.email = email
        self.foto = foto