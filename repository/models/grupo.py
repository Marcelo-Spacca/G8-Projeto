from repository.models.base import Modelo, agora


class Grupo(Modelo):
    """Grupo de alunos de uma turma que faz UMA pesquisa junto.

    título/objetivo ficam guardados no grupo; a pesquisa dele só nasce quando o primeiro convite é
    aceito (ou o professor atribui alguém), isto é, quando o grupo passa a ter 2 integrantes."""

    COLECAO = "grupos"
    CAMPOS = {
        "nome": None,
        "titulo": None,
        "objetivo": None,
        "data_criacao": agora,
        "turma_id": None,
        "criador_id": None,
    }
    RELACOES = {"turma": None, "criador": None, "membros": list, "convites": list, "pesquisa": None}

    @property
    def alunos(self):
        """Integrantes em ordem alfabética (precisa de membros e aluno carregados)."""
        return sorted((m.aluno for m in self.membros), key=lambda a: (a.nome.lower(), len(a.id), a.id))


class GrupoAluno(Modelo):
    """Integrante de um grupo. Id do documento: 'grupo_aluno' (impede repetir)."""

    COLECAO = "grupo_alunos"
    CAMPOS = {"grupo_id": None, "aluno_id": None, "data_entrada": agora}
    RELACOES = {"grupo": None, "aluno": None}


class ConviteGrupo(Modelo):
    """Convite de um integrante do grupo para outro aluno da mesma turma. Id: 'grupo_aluno'."""

    COLECAO = "convites"
    CAMPOS = {
        "status": "pendente",  # pendente | aceito | recusado
        "data_criacao": agora,
        "data_resposta": None,
        "grupo_id": None,
        "aluno_id": None,  # o convidado
        "convidado_por_id": None,
    }
    RELACOES = {"grupo": None, "aluno": None, "convidado_por": None}
