from repository.models.base import Modelo, agora


class Turma(Modelo):
    """Uma cadeira do professor. O aluno entra com o 'codigo' e só então cria pesquisas nela."""

    COLECAO = "turmas"
    CAMPOS = {
        "nome": None,
        "codigo": None,  # código de entrada, único
        "permite_grupos": False,
        "data_criacao": agora,
        "professor_id": None,
    }
    RELACOES = {"professor": None, "matriculas": list, "grupos": list, "pesquisas": list}

    @property
    def alunos(self):
        """Alunos matriculados, em ordem alfabética (precisa de matriculas e aluno carregados)."""
        return sorted((m.aluno for m in self.matriculas), key=lambda a: (a.nome.lower(), len(a.id), a.id))


class Matricula(Modelo):
    """Aluno dentro de uma turma. Um aluno pode estar em várias turmas.
    O id do documento é 'turma_aluno': é isso que impede a matrícula repetida."""

    COLECAO = "matriculas"
    CAMPOS = {"turma_id": None, "aluno_id": None, "data_entrada": agora}
    RELACOES = {"turma": None, "aluno": None}
