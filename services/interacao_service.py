from repository.interacao_repository import InteracaoRepository
from repository.models import Interacao
from services.erros import RegraViolada
from services.pesquisa_service import PesquisaService


def exigir_pesquisa_aberta(pesquisa):
    if pesquisa.status == "concluida":
        raise RegraViolada("Esta pesquisa já foi concluída e não pode mais ser alterada.")


def _validar_textos(ferramenta_ia, pergunta, resposta):
    ferramenta_ia = (ferramenta_ia or "").strip()
    pergunta = (pergunta or "").strip()
    resposta = (resposta or "").strip()
    if not ferramenta_ia:
        raise RegraViolada("Informe a ferramenta de IA usada.")
    if not pergunta:
        raise RegraViolada("Informe a pergunta feita à IA.")
    if not resposta:
        raise RegraViolada("Informe a resposta da IA.")
    return ferramenta_ia, pergunta, resposta


class InteracaoService:
    def __init__(self):
        self.repo = InteracaoRepository()
        self.pesquisas = PesquisaService()

    def registrar(self, pesquisa_id, ferramenta_ia, pergunta, resposta):
        pesquisa = self.pesquisas.obter(pesquisa_id)
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída e não aceita novas interações.")

        ferramenta_ia, pergunta, resposta = _validar_textos(ferramenta_ia, pergunta, resposta)
        interacao = Interacao(
            ferramenta_ia=ferramenta_ia,
            pergunta=pergunta,
            resposta=resposta,
            pesquisa_id=pesquisa.id,
        )
        return self.repo.salvar(interacao)

    def listar(self, pesquisa_id):
        pesquisa = self.pesquisas.obter(pesquisa_id)
        return self.repo.listar_por_pesquisa(pesquisa.id)

    def obter(self, interacao_id):
        """Interação do aluno logado, com fontes e trechos (RF27)."""
        interacao = self.repo.buscar_por_id(interacao_id)
        if interacao is None:
            raise RegraViolada("Interação não encontrada.")
        try:
            self.pesquisas.obter(interacao.pesquisa_id)  # confere login e dono
        except RegraViolada as erro:
            if "não encontrada" in str(erro):
                # Interação de outro aluno é tratada como inexistente.
                raise RegraViolada("Interação não encontrada.") from None
            raise
        return interacao

    def editar(self, interacao_id, ferramenta_ia, pergunta, resposta):  # RF13
        """Corrige ferramenta, pergunta e resposta. As fontes ligadas não mudam."""
        interacao = self.obter(interacao_id)
        exigir_pesquisa_aberta(self.pesquisas.obter(interacao.pesquisa_id))
        ferramenta_ia, pergunta, resposta = _validar_textos(ferramenta_ia, pergunta, resposta)
        self.repo.atualizar(interacao.id, ferramenta_ia, pergunta, resposta)
        return self.obter(interacao.id)

    def excluir(self, interacao_id):  # RF14
        """Apaga a interação e, junto, as fontes e trechos dela.
        A confirmação com o usuário é feita pela tela antes de chamar este método."""
        interacao = self.obter(interacao_id)
        exigir_pesquisa_aberta(self.pesquisas.obter(interacao.pesquisa_id))
        self.repo.excluir(interacao.id)
