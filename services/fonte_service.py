from repository.fonte_repository import FonteRepository
from repository.models import Fonte, Trecho
from services.erros import RegraViolada
from services.interacao_service import InteracaoService, exigir_pesquisa_aberta

RESULTADOS = ("verificada", "incorreta")


def _limpar(texto):
    texto = (texto or "").strip()
    return texto or None


def _novo_trecho(trecho, localizacao):
    trecho = _limpar(trecho)
    if trecho is None:
        raise RegraViolada("Informe o trecho do seu texto.")
    return Trecho(trecho_citado=trecho, localizacao=_limpar(localizacao))


class FonteService:
    def __init__(self):
        self.repo = FonteRepository()
        self.interacoes = InteracaoService()

    def adicionar(self, interacao_id, referencia):
        """Registra uma fonte citada pela IA numa interação (nasce 'nao_verificada')."""
        interacao = self.interacoes.obter(interacao_id)
        exigir_pesquisa_aberta(self.interacoes.pesquisas.obter(interacao.pesquisa_id))
        referencia = _limpar(referencia)
        if referencia is None:
            raise RegraViolada("Informe a referência da fonte.")
        return self.repo.salvar(Fonte(referencia=referencia, interacao_id=interacao.id))

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

    def verificar(self, fonte_id, resultado, anotacao=None, trecho=None, localizacao=None):
        """Registra a verificação de uma fonte.

        RF18: a anotação do que o aluno encontrou fica salva na fonte.
        RF26: se a fonte foi confirmada, o aluno pode informar o trecho do texto
              em que a usou; o trecho fica salvo junto da fonte.
        """
        if resultado not in RESULTADOS:
            raise RegraViolada("Escolha o resultado: verificada ou incorreta.")
        fonte = self.obter(fonte_id)
        novo_trecho = None
        if _limpar(trecho) is not None:
            if resultado != "verificada":
                raise RegraViolada("Só é possível ligar um trecho a uma fonte verificada.")
            novo_trecho = _novo_trecho(trecho, localizacao)
        self.repo.registrar_verificacao(fonte.id, resultado, _limpar(anotacao), novo_trecho)
        return self.obter(fonte.id)

    def ligar_trecho(self, fonte_id, trecho, localizacao=None):  # RF26
        """Liga mais um trecho do texto a uma fonte que já foi verificada."""
        fonte = self.obter(fonte_id)
        if fonte.status != "verificada":
            raise RegraViolada("Só é possível ligar um trecho a uma fonte verificada.")
        novo = _novo_trecho(trecho, localizacao)
        novo.fonte_id = fonte.id
        return self.repo.adicionar_trecho(novo)
