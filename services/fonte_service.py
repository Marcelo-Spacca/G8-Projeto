from repository.fonte_repository import FonteRepository
from repository.models import Fonte, Trecho
from services.erros import RegraViolada
from services.interacao_service import InteracaoService, exigir_pesquisa_aberta

RESULTADOS = ("nao_verificada", "verificada", "incorreta")  # RF17: o status pode ir de um a outro


def _limpar(texto):
    texto = (texto or "").strip()
    return texto or None


def _novo_trecho(trecho, localizacao):
    trecho = _limpar(trecho)
    if trecho is None:
        raise RegraViolada("Informe o trecho do seu texto.")
    return Trecho(trecho_citado=trecho, localizacao=_limpar(localizacao))


def contar_status(fontes):
    """Quantas fontes há em cada status (RF19). Serve para qualquer lista de fontes já carregada."""
    contagem = {"verificada": 0, "incorreta": 0, "nao_verificada": 0}
    for fonte in fontes:
        contagem[fonte.status] += 1
    return contagem


class FonteService:
    def __init__(self):
        self.repo = FonteRepository()
        self.interacoes = InteracaoService()

    def adicionar(self, interacao_id, referencia, link=None):
        """RF15/RF16: registra uma fonte citada pela IA numa interação. Ela nasce 'nao_verificada'."""
        interacao = self.interacoes.obter(interacao_id)
        exigir_pesquisa_aberta(self.interacoes.pesquisas.obter(interacao.pesquisa_id))
        referencia = _limpar(referencia)
        if referencia is None:
            raise RegraViolada("Informe a referência da fonte.")
        return self.repo.salvar(
            Fonte(referencia=referencia, link=_limpar(link), interacao_id=interacao.id)
        )

    def obter(self, fonte_id):
        fonte = self.repo.buscar_por_id(fonte_id)
        if fonte is None:
            raise RegraViolada("Fonte não encontrada.")
        try:
            self.interacoes.obter(fonte.interacao_id)  # confere login e dono
        except RegraViolada as erro:
            if "não encontrada" in str(erro):
                raise RegraViolada("Fonte não encontrada.") from None
            raise
        return fonte

    def _obter_editavel(self, fonte_id):
        """A fonte do aluno logado, em uma pesquisa que ainda não foi concluída.
        Depois de concluída a pesquisa vira o que foi entregue ao professor e não muda mais."""
        fonte = self.obter(fonte_id)
        interacao = self.interacoes.obter(fonte.interacao_id)
        exigir_pesquisa_aberta(self.interacoes.pesquisas.obter(interacao.pesquisa_id))
        return fonte

    def listar(self, interacao_id):
        """RF19: as fontes de uma interação, na ordem em que foram cadastradas, com status e trechos."""
        interacao = self.interacoes.obter(interacao_id)
        return sorted(interacao.fontes, key=lambda f: f.id)

    def verificar(self, fonte_id, resultado, anotacao=None, trecho=None, localizacao=None):
        """Registra a verificação de uma fonte.

        RF17: o aluno confere a fonte e a marca como 'verificada' ou 'incorreta'
              (ou volta para 'nao_verificada').
        RF18: a anotação do que o aluno encontrou fica salva na fonte.
        RF26: se a fonte foi confirmada, o aluno pode informar o trecho do texto
              em que a usou; o trecho fica salvo junto da fonte.
        """
        if resultado not in RESULTADOS:
            raise RegraViolada("Escolha o resultado: verificada, incorreta ou não verificada.")
        fonte = self._obter_editavel(fonte_id)
        novo_trecho = None
        if _limpar(trecho) is not None:
            if resultado != "verificada":
                raise RegraViolada("Só é possível ligar um trecho a uma fonte verificada.")
            novo_trecho = _novo_trecho(trecho, localizacao)
        self.repo.registrar_verificacao(fonte.id, resultado, _limpar(anotacao), novo_trecho)
        return self.obter(fonte.id)

    def ligar_trecho(self, fonte_id, trecho, localizacao=None):  # RF26
        """Liga mais um trecho do texto a uma fonte que já foi verificada."""
        fonte = self._obter_editavel(fonte_id)
        if fonte.status != "verificada":
            raise RegraViolada("Só é possível ligar um trecho a uma fonte verificada.")
        novo = _novo_trecho(trecho, localizacao)
        novo.fonte_id = fonte.id
        return self.repo.adicionar_trecho(novo)
