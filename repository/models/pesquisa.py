from repository.models.base import Modelo, agora


class Pesquisa(Modelo):
    COLECAO = "pesquisas"
    CAMPOS = {
        "titulo": None,
        "objetivo": None,
        # em_andamento: o aluno edita (inclui a pesquisa devolvida) | entregue: o professor revisa
        # | concluida: o professor aceitou e nada mais muda
        "status": "em_andamento",
        "data_criacao": agora,
        "data_entrega": None,
        "data_conclusao": None,  # quando o professor aceitou
        "mensagem_devolucao": None,  # por que o professor devolveu
        "data_devolucao": None,
        # Individual: aluno_id preenchido. De grupo: grupo_id preenchido (um grupo tem uma só pesquisa).
        "aluno_id": None,
        "grupo_id": None,
        "turma_id": None,  # a cadeira a que a pesquisa pertence
    }
    RELACOES = {"aluno": None, "grupo": None, "turma": None, "interacoes": list, "relatorio": None}

    @property
    def devolvida(self):
        """Pesquisa que o professor devolveu e o aluno ainda não entregou de novo."""
        return self.status == "em_andamento" and bool(self.mensagem_devolucao)

    @property
    def de_grupo(self):
        return self.grupo_id is not None

    @property
    def autor(self):
        """Quem assina a pesquisa: o nome do aluno ou o do grupo (precisa de aluno/grupo carregado)."""
        return self.grupo.nome if self.de_grupo else self.aluno.nome
