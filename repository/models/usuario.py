from repository.models.base import Modelo


class Usuario(Modelo):
    COLECAO = "usuarios"
    CAMPOS = {
        "nome": None,
        "email": None,
        "senha_hash": None,  # nunca a senha em texto puro
        "tipo": None,  # 'aluno' ou 'professor'
    }
    # o aluno entra em turmas pelas matrículas (ver models/turma.py)
    RELACOES = {"pesquisas": list}
