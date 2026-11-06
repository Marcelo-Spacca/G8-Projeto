# Importar todas as classes aqui garante que o SQLAlchemy conhece todas as tabelas
# e consegue resolver as relações entre elas. Ao criar um model novo, adicione-o aqui.
from repository.models.fonte import Fonte
from repository.models.interacao import Interacao
from repository.models.pesquisa import Pesquisa
from repository.models.relatorio import Relatorio
from repository.models.trecho import Trecho
from repository.models.turma import Turma
from repository.models.usuario import Usuario

__all__ = ["Fonte", "Interacao", "Pesquisa", "Relatorio", "Trecho", "Turma", "Usuario"]
