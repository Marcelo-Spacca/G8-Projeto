from repository.models.base import Modelo, agora


class Interacao(Modelo):
    COLECAO = "interacoes"
    CAMPOS = {
        "ferramenta_ia": None,
        "pergunta": None,
        "resposta": None,
        "data_registro": agora,
        # Revisão do professor: o comentário só ele escreve; o aluno só lê. Interação confirmada
        # fica fechada: o aluno não altera mais (precisa criar uma nova).
        "comentario_professor": None,
        "data_comentario": None,
        "confirmada": False,
        "pesquisa_id": None,
    }
    RELACOES = {"pesquisa": None, "fontes": list}
