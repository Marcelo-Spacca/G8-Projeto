from dataclasses import dataclass

from repository.pesquisa_repository import PesquisaRepository
from repository.relatorio_repository import RelatorioRepository
from services.erros import RegraViolada
from services.fonte_service import contar_status
from services.sessao import sessao


def exigir_professor():
    if not sessao.logado:
        raise RegraViolada("Entre na sua conta para continuar.")
    if sessao.usuario.tipo != "professor":
        raise RegraViolada("Esta ação é exclusiva de professores.")
    return sessao.usuario


@dataclass
class RelatorioGerado:
    """O que a tela precisa para mostrar o relatório.
    'pesquisa' já vem com aluno, interações, fontes e trechos carregados."""

    relatorio: object
    pesquisa: object

    @property
    def entregue(self):
        """True depois que o aluno entrega a pesquisa ao professor (RF10). Antes é só uma prévia."""
        return self.pesquisa.status in ("entregue", "concluida")

    @property
    def concluida(self):
        """True depois que o professor aceita a pesquisa."""
        return self.pesquisa.status == "concluida"

    @property
    def interacoes(self):
        return sorted(self.pesquisa.interacoes, key=lambda i: (i.data_registro, i.id))

    @property
    def fontes(self):
        return [f for i in self.interacoes for f in sorted(i.fontes, key=lambda f: f.id)]

    def contagem_status(self):
        return contar_status(self.fontes)


class RelatorioService:
    def __init__(self):
        self.repo = RelatorioRepository()
        self.pesquisas = PesquisaRepository()

    def gerar(self, pesquisa_id):
        """RF20/RF21/RF28: monta o relatório só com o que já foi registrado, sem digitação extra:
        interações, fontes, status, anotações e o trecho em que cada fonte foi usada.
        RF22: o relatório é sempre o único ligado a esta pesquisa.

        RF03: o aluno vê o relatório (ou a prévia dele) só das próprias pesquisas; o professor vê
        apenas as pesquisas já entregues das turmas dele (o relatório de pesquisa em andamento fica bloqueado). Qualquer outro caso é tratado como inexistente.
        """
        if not sessao.logado:
            raise RegraViolada("Entre na sua conta para continuar.")
        pesquisa = self.repo.dados_da_pesquisa(pesquisa_id)
        usuario = sessao.usuario
        if usuario.tipo == "professor":
            visivel = (
                pesquisa is not None
                and pesquisa.status in ("entregue", "concluida")
                and self.pesquisas.professor_da_pesquisa(pesquisa.id) == usuario.id
            )
        else:  # a própria pesquisa ou a de um grupo de que o aluno faz parte
            visivel = pesquisa is not None and self.pesquisas.aluno_acessa(pesquisa.id, usuario.id)
        if not visivel:
            raise RegraViolada("Pesquisa não encontrada.")
        relatorio = self.repo.garantir(pesquisa.id)
        return RelatorioGerado(relatorio=relatorio, pesquisa=pesquisa)
