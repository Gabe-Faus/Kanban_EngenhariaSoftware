
class Usuario:
    def __init__(self, nome, email, senha, foto, id=None):
        self.id = id  # Set by database after insertion
        self.nome = nome
        self.email = email
        self.senha = senha
        self.foto = foto


class Quadro:
    def __init__(self, nome, descricao, data_criacao, id=None):
        self.id = id  # Set by database after insertion
        self.nome = nome
        self.descricao = descricao
        self.data_criacao = data_criacao


class Raia:
    def __init__(self, qtd_max, nome, id_quadro, id=None):
        self.id = id  # Set by database after insertion
        self.qtd_max = qtd_max
        self.nome = nome
        self.id_quadro = id_quadro


class Cartao:
    def __init__(self, data_incio, data_final, data_criacao, nome, ordem, id_raia, id_cor, descricao, id=None):
        self.id = id  # Set by database after insertion
        self.data_incio = data_incio
        self.data_final = data_final
        self.data_criacao = data_criacao
        self.nome = nome
        self.ordem = ordem
        self.id_raia = id_raia
        self.id_cor = id_cor
        self.descricao = descricao

class Cor:
    def __init__(self, nome, id=None):
        self.id = id  # Set by database after insertion
        self.nome = nome
