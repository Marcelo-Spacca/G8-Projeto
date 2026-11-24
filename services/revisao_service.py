"""Área do professor: acompanhar as pesquisas dos alunos e revisar as que foram entregues.

Fluxo: o aluno entrega; o professor julga as fontes, comenta e confirma as interações, e então
aceita (a pesquisa fica concluída) ou devolve com uma mensagem (volta a 'em andamento' para o
aluno ajustar). Pesquisa em andamento o professor só acompanha: não altera nada nela.
"""
from repository.interacao_repository import InteracaoRepository
from repository.fonte_repository import FonteRepository
from repository.pesquisa_repository import PesquisaRepository
from repository.relatorio_repository import RelatorioRepository
from services.erros import RegraViolada
from services.fonte_service import RESULTADOS, contar_status
from services.relatorio_service import exigir_professor


def _limpar(texto):
    texto = (texto or "").strip()
    return texto or None


class RevisaoService:
    def __init__(self):
        self.pesquisas = PesquisaRepository()
        self.interacoes = InteracaoRepository()
        self.fontes = FonteRepository()
        self.relatorios = RelatorioRepository()

    # ---------------------------------------------------------------- acompanhar (só leitura)
    def _conferir_dono(self, pesquisa_id):
        """O professor só alcança pesquisas das turmas dele; as outras são tratadas como inexistentes."""
        professor = exigir_professor()
        if self.pesquisas.professor_da_pesquisa(pesquisa_id) != professor.id:
            raise RegraViolada("Pesquisa não encontrada.")
        return professor

    def listar_todas(self, turma_id=None):
        """As pesquisas das turmas do professor (ou só de uma turma, para filtrar), com aluno/grupo,
        interações e fontes já carregados."""
        professor = exigir_professor()
        return self.pesquisas.listar_do_professor(professor.id, turma_id)

    def contagem_fontes(self, pesquisa):
        return contar_status(f for i in pesquisa.interacoes for f in i.fontes)

    def obter_pesquisa(self, pesquisa_id):
        """A pesquisa de qualquer aluno, com interações, fontes e trechos."""
        self._conferir_dono(pesquisa_id)
        pesquisa = self.relatorios.dados_da_pesquisa(pesquisa_id)
        if pesquisa is None:
            raise RegraViolada("Pesquisa não encontrada.")
        pesquisa.interacoes.sort(key=lambda i: (i.data_registro, i.id))
        return pesquisa

    def obter_interacao(self, interacao_id):
        exigir_professor()
        interacao = self.interacoes.buscar_por_id(interacao_id)
        if interacao is None:
            raise RegraViolada("Interação não encontrada.")
        try:
            self._conferir_dono(interacao.pesquisa_id)
        except RegraViolada:
            raise RegraViolada("Interação não encontrada.") from None
        return interacao

    # ---------------------------------------------------------------- revisar (pesquisa entregue)
    def _pesquisa_em_revisao(self, pesquisa_id):
        self._conferir_dono(pesquisa_id)
        pesquisa = self.pesquisas.buscar_por_id(pesquisa_id)
        if pesquisa is None:
            raise RegraViolada("Pesquisa não encontrada.")
        if pesquisa.status == "em_andamento":
            raise RegraViolada("O aluno ainda não entregou esta pesquisa: você pode acompanhá-la, mas não alterá-la.")
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída e não pode mais ser alterada.")
        return pesquisa

    def _interacao_em_revisao(self, interacao_id):
        interacao = self.obter_interacao(interacao_id)
        self._pesquisa_em_revisao(interacao.pesquisa_id)
        return interacao

    def julgar_fonte(self, fonte_id, resultado, anotacao=None):
        """O professor confere a fonte: verificada, incorreta ou volta a não verificada.
        A anotação dele fica na fonte e o aluno a lê. Interação confirmada precisa ser reaberta."""
        exigir_professor()
        if resultado not in RESULTADOS:
            raise RegraViolada("Escolha o resultado: verificada, incorreta ou não verificada.")
        fonte = self.fontes.buscar_por_id(fonte_id)
        if fonte is None:
            raise RegraViolada("Fonte não encontrada.")
        interacao = self._interacao_em_revisao(fonte.interacao_id)
        if interacao.confirmada:
            raise RegraViolada("Esta interação está confirmada. Reabra-a para alterar a verificação das fontes.")
        self.fontes.registrar_verificacao(fonte.id, resultado, _limpar(anotacao), None, pelo_professor=True)
        return self.fontes.buscar_por_id(fonte.id)

    def comentar_interacao(self, interacao_id, comentario):
        """Comentário do professor na interação (só o aluno lê). Texto vazio apaga o comentário."""
        exigir_professor()
        interacao = self._interacao_em_revisao(interacao_id)
        self.interacoes.registrar_comentario(interacao.id, _limpar(comentario))
        return self.obter_interacao(interacao.id)

    def confirmar_interacao(self, interacao_id):
        """Fecha a interação: o aluno não a altera mais. Exige que todas as fontes tenham sido julgadas."""
        exigir_professor()
        interacao = self._interacao_em_revisao(interacao_id)
        if interacao.confirmada:
            raise RegraViolada("Esta interação já está confirmada.")
        if contar_status(interacao.fontes)["nao_verificada"]:
            raise RegraViolada("Julgue todas as fontes (verificada ou incorreta) antes de confirmar a interação.")
        self.interacoes.definir_confirmada(interacao.id, True)
        return self.obter_interacao(interacao.id)

    def reabrir_interacao(self, interacao_id):
        exigir_professor()
        interacao = self._interacao_em_revisao(interacao_id)
        if not interacao.confirmada:
            raise RegraViolada("Esta interação não está confirmada.")
        self.interacoes.definir_confirmada(interacao.id, False)
        return self.obter_interacao(interacao.id)

    def aceitar(self, pesquisa_id):
        """Conclui a pesquisa: tudo fica fechado e o relatório é carimbado."""
        exigir_professor()
        pesquisa = self._pesquisa_em_revisao(pesquisa_id)
        return self.pesquisas.aceitar(pesquisa.id)

    def devolver(self, pesquisa_id, mensagem):
        """Devolve ao aluno com o motivo (obrigatório). A pesquisa volta a 'em andamento'."""
        exigir_professor()
        pesquisa = self._pesquisa_em_revisao(pesquisa_id)
        mensagem = _limpar(mensagem)
        if mensagem is None:
            raise RegraViolada("Escreva uma mensagem explicando por que a pesquisa foi devolvida.")
        return self.pesquisas.devolver(pesquisa.id, mensagem)
