from repository import armazenamento
from repository.armazenamento import ErroDeIntegridade, agora
from repository.carga import carregar_pesquisas, mais_recentes_primeiro
from repository.cascata import apagar_pesquisas
from repository.models import Pesquisa, Relatorio

STATUS = ("em_andamento", "entregue", "concluida")


def id_da_pesquisa_do_grupo(grupo_id):
    """Cada grupo tem uma só pesquisa: o id do documento é derivado do grupo, e é isso que impede
    uma segunda."""
    return f"grupo-{grupo_id}"


def _atualizada(pesquisa_id):
    return Pesquisa.de_dict(armazenamento.loja().obter("pesquisas", pesquisa_id))


class PesquisaRepository:
    def salvar(self, pesquisa):
        if pesquisa.status not in STATUS:
            raise ErroDeIntegridade(f"status de pesquisa inválido: {pesquisa.status!r}")
        # a pesquisa é de um aluno OU de um grupo, nunca dos dois nem de ninguém
        if (pesquisa.aluno_id is None) == (pesquisa.grupo_id is None):
            raise ErroDeIntegridade("a pesquisa precisa ser de um aluno ou de um grupo (só um dos dois)")
        loja = armazenamento.loja()
        pesquisa.id = (
            id_da_pesquisa_do_grupo(pesquisa.grupo_id) if pesquisa.de_grupo else loja.novo_id()
        )
        lote = loja.lote()
        lote.criar("pesquisas", pesquisa.id, pesquisa.para_dict())
        if pesquisa.relatorio is not None:  # RF20/RF22: o relatório nasce junto
            pesquisa.relatorio.id = pesquisa.id
            pesquisa.relatorio.pesquisa_id = pesquisa.id
            lote.criar("relatorios", pesquisa.id, pesquisa.relatorio.para_dict())
        lote.confirmar()
        return pesquisa

    def atualizar(self, pesquisa_id, titulo, objetivo):
        """Grava o novo título e objetivo e devolve a pesquisa atualizada."""
        armazenamento.loja().atualizar("pesquisas", pesquisa_id, {"titulo": titulo, "objetivo": objetivo})
        return _atualizada(pesquisa_id)

    def buscar_por_id(self, pesquisa_id):
        """A pesquisa com a turma e, se for de grupo, o grupo e os integrantes (para a tela)."""
        doc = armazenamento.loja().obter("pesquisas", pesquisa_id)
        return carregar_pesquisas([doc], aluno=True, turma=True, grupo=True)[0] if doc else None

    def aluno_acessa(self, pesquisa_id, aluno_id):
        """True se a pesquisa é do aluno ou do grupo de que ele faz parte."""
        loja = armazenamento.loja()
        doc = loja.obter("pesquisas", pesquisa_id)
        if doc is None:
            return False
        if doc.get("aluno_id") == str(aluno_id):
            return True
        grupo_id = doc.get("grupo_id")
        return grupo_id is not None and loja.obter("grupo_alunos", f"{grupo_id}_{aluno_id}") is not None

    def professor_da_pesquisa(self, pesquisa_id):
        """Id do professor dono da turma da pesquisa (None se a pesquisa não existe ou não tem turma)."""
        loja = armazenamento.loja()
        doc = loja.obter("pesquisas", pesquisa_id)
        if doc is None or doc.get("turma_id") is None:
            return None
        turma = loja.obter("turmas", doc["turma_id"])
        return turma["professor_id"] if turma else None

    def entregar(self, pesquisa_id):
        """O aluno entrega a pesquisa ao professor: ela passa a 'entregue' e trava para o aluno."""
        armazenamento.loja().atualizar("pesquisas", pesquisa_id, {"status": "entregue", "data_entrega": agora()})
        return _atualizada(pesquisa_id)

    def devolver(self, pesquisa_id, mensagem):
        """O professor devolve: a pesquisa volta a 'em_andamento' (incompleta) com o motivo.
        As interações já confirmadas continuam fechadas; as outras o aluno pode ajustar."""
        armazenamento.loja().atualizar(
            "pesquisas",
            pesquisa_id,
            {
                "status": "em_andamento",
                "data_entrega": None,
                "mensagem_devolucao": mensagem,
                "data_devolucao": agora(),
            },
        )
        return _atualizada(pesquisa_id)

    def aceitar(self, pesquisa_id):
        """RF10: o professor aceita. A pesquisa passa a 'concluida', todas as interações ficam
        fechadas e o relatório é carimbado, tudo no mesmo lote."""
        loja = armazenamento.loja()
        momento = agora()
        lote = loja.lote()
        lote.atualizar(
            "pesquisas",
            pesquisa_id,
            {"status": "concluida", "data_conclusao": momento, "mensagem_devolucao": None},
        )
        for interacao in loja.consultar("interacoes", pesquisa_id=pesquisa_id):
            lote.atualizar("interacoes", interacao["id"], {"confirmada": True})
        if loja.obter("relatorios", pesquisa_id) is None:  # pesquisas antigas, sem relatório
            lote.criar("relatorios", pesquisa_id, Relatorio(pesquisa_id=pesquisa_id, data_geracao=momento).para_dict())
        else:
            lote.atualizar("relatorios", pesquisa_id, {"data_geracao": momento})
        lote.confirmar()
        return _atualizada(pesquisa_id)

    def listar_do_professor(self, professor_id, turma_id=None):
        """Área do professor: as pesquisas das turmas dele (ou só de uma), com aluno/grupo,
        interações e fontes carregados, da atividade mais recente para a mais antiga."""
        loja = armazenamento.loja()
        turmas = [t["id"] for t in loja.consultar("turmas", professor_id=professor_id)]
        if turma_id is not None:
            turmas = [t for t in turmas if t == str(turma_id)]
        docs = loja.consultar_em("pesquisas", "turma_id", turmas)
        pesquisas = carregar_pesquisas(docs, aluno=True, turma=True, grupo=True, interacoes=True, fontes=True)
        return mais_recentes_primeiro(pesquisas, lambda p: p.data_entrega or p.data_criacao)

    def excluir(self, pesquisa_id):
        """RF09: apaga junto relatório, interações, fontes e trechos."""
        loja = armazenamento.loja()
        lote = loja.lote()
        apagar_pesquisas(loja, lote, [pesquisa_id])
        lote.confirmar()

    def listar_por_aluno(self, aluno_id, turma_id):
        """Pesquisas individuais do aluno na turma, da mais recente para a mais antiga."""
        docs = armazenamento.loja().consultar("pesquisas", aluno_id=str(aluno_id), turma_id=str(turma_id))
        return mais_recentes_primeiro(carregar_pesquisas(docs), lambda p: p.data_criacao)

    def listar_de_grupos_do_aluno(self, aluno_id, turma_id):
        """Pesquisas dos grupos de que o aluno participa na turma, com o grupo carregado."""
        loja = armazenamento.loja()
        grupos = [m["grupo_id"] for m in loja.consultar("grupo_alunos", aluno_id=str(aluno_id))]
        docs = loja.consultar_em("pesquisas", "grupo_id", grupos, turma_id=str(turma_id))
        return mais_recentes_primeiro(carregar_pesquisas(docs, grupo=True), lambda p: p.data_criacao)
