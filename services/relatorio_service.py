from dataclasses import dataclass

from repository.pesquisa_repository import PesquisaRepository
from repository.relatorio_repository import RelatorioRepository
from services.erros import RegraViolada
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
    def interacoes(self):
        return sorted(self.pesquisa.interacoes, key=lambda i: (i.data_registro, i.id))

    @property
    def fontes(self):
        return [f for i in self.interacoes for f in i.fontes]

    def contagem_status(self):
        contagem = {"verificada": 0, "incorreta": 0, "nao_verificada": 0}
        for fonte in self.fontes:
            contagem[fonte.status] += 1
        return contagem


class RelatorioService:
    def __init__(self):
        self.repo = RelatorioRepository()
        self.pesquisas = PesquisaRepository()

    def listar_pesquisas(self):
        """Área do professor: todas as pesquisas, com o nome do aluno."""
        exigir_professor()
        return self.pesquisas.listar_todas()

    def gerar(self, pesquisa_id):
        """RF20: monta o relatório só com o que já foi registrado, sem digitação extra.
        RF22: o relatório é sempre o único ligado a esta pesquisa.

        Professor vê o de qualquer pesquisa; aluno, só o das próprias.
        """
        if not sessao.logado:
            raise RegraViolada("Entre na sua conta para continuar.")
        pesquisa = self.repo.dados_da_pesquisa(pesquisa_id)
        usuario = sessao.usuario
        if pesquisa is None or (usuario.tipo != "professor" and pesquisa.aluno_id != usuario.id):
            raise RegraViolada("Pesquisa não encontrada.")
        relatorio = self.repo.registrar_geracao(pesquisa.id)
        return RelatorioGerado(relatorio=relatorio, pesquisa=pesquisa)
