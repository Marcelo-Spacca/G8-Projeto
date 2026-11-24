from repository import armazenamento
from repository.armazenamento import Duplicado
from repository.carga import carregar_pesquisas
from repository.models import Relatorio


class RelatorioRepository:
    def buscar_por_pesquisa(self, pesquisa_id):
        doc = armazenamento.loja().obter("relatorios", pesquisa_id)  # o id do relatório é o da pesquisa
        return Relatorio.de_dict(doc) if doc else None

    def garantir(self, pesquisa_id):
        """RF22: devolve o relatório da pesquisa (cria se ainda não existir, só para pesquisas
        antigas). A data de geração só muda quando a pesquisa é concluída (RF10)."""
        existente = self.buscar_por_pesquisa(pesquisa_id)
        if existente is not None:
            return existente
        relatorio = Relatorio(id=str(pesquisa_id), pesquisa_id=str(pesquisa_id))
        try:
            armazenamento.loja().criar("relatorios", relatorio.id, relatorio.para_dict())
        except Duplicado:  # alguém criou no mesmo instante
            return self.buscar_por_pesquisa(pesquisa_id)
        return relatorio

    def dados_da_pesquisa(self, pesquisa_id):
        """Pesquisa com aluno, turma, grupo, interações, fontes e trechos já carregados (RF20)."""
        doc = armazenamento.loja().obter("pesquisas", pesquisa_id)
        if doc is None:
            return None
        return carregar_pesquisas(
            [doc], aluno=True, turma=True, grupo=True, interacoes=True, fontes=True, trechos=True
        )[0]
