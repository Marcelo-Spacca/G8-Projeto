# As classes de dados do programa (cada uma é uma coleção do Firestore).
from repository.models.fonte import Fonte
from repository.models.grupo import ConviteGrupo, Grupo, GrupoAluno
from repository.models.interacao import Interacao
from repository.models.pesquisa import Pesquisa
from repository.models.relatorio import Relatorio
from repository.models.trecho import Trecho
from repository.models.turma import Matricula, Turma
from repository.models.usuario import Usuario

__all__ = [
    "ConviteGrupo", "Fonte", "Grupo", "GrupoAluno", "Interacao", "Matricula",
    "Pesquisa", "Relatorio", "Trecho", "Turma", "Usuario",
]
