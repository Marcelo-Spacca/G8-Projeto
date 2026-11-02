class Sessao:

    def __init__(self):
        self.usuario = None

    @property
    def logado(self):
        return self.usuario is not None

    def iniciar(self, usuario):
        self.usuario = usuario

    def encerrar(self):
        self.usuario = None


# Uma única sessão para o programa inteiro; os services e as telas importam esta.
sessao = Sessao()
