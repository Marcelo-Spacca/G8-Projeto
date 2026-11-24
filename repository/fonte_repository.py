from repository import armazenamento
from repository.armazenamento import agora
from repository.carga import chave_id
from repository.models import Fonte, Interacao, Trecho


def _apagar_trechos(loja, lote, fonte_id):
    for doc in loja.consultar("trechos", fonte_id=fonte_id):
        lote.apagar("trechos", doc["id"])


class FonteRepository:
    def salvar(self, fonte):
        loja = armazenamento.loja()
        fonte.id = loja.novo_id()
        loja.criar("fontes", fonte.id, fonte.para_dict())
        return fonte

    def buscar_por_id(self, fonte_id):
        loja = armazenamento.loja()
        doc = loja.obter("fontes", fonte_id)
        if doc is None:
            return None
        fonte = Fonte.de_dict(doc)
        interacao = loja.obter("interacoes", fonte.interacao_id)
        fonte.interacao = Interacao.de_dict(interacao) if interacao else None
        fonte.trechos = self.listar_trechos(fonte.id)
        for trecho in fonte.trechos:
            trecho.fonte = fonte
        return fonte

    def registrar_verificacao(self, fonte_id, status, anotacao, trecho, pelo_professor=False):
        """Grava o resultado da verificação (RF17), a anotação (RF18) e, se houver, o trecho
        ligado (RF26) num único lote: ou salva tudo, ou nada.

        Trecho só faz sentido em fonte verificada: se a fonte deixa de ser 'verificada',
        os trechos ligados a ela saem junto."""
        loja = armazenamento.loja()
        lote = loja.lote()
        campos = {
            "status": status,
            "julgada_pelo_professor": pelo_professor,
            "data_verificacao": None if status == "nao_verificada" else agora(),
        }
        if anotacao is not None:
            campos["anotacao_correcao"] = anotacao
        lote.atualizar("fontes", fonte_id, campos)
        if status != "verificada":
            _apagar_trechos(loja, lote, fonte_id)
        if trecho is not None:
            trecho.fonte_id = fonte_id
            trecho.id = loja.novo_id()
            lote.criar("trechos", trecho.id, trecho.para_dict())
        lote.confirmar()

    def atualizar(self, fonte_id, referencia, link, zerar_verificacao):
        """Grava a nova referência e o novo link. Se o conteúdo mudou e a fonte já estava julgada,
        a verificação antiga deixa de valer: volta a 'nao_verificada' e os trechos ligados saem
        (o aluno confere de novo a fonte corrigida). Tudo num único lote."""
        loja = armazenamento.loja()
        lote = loja.lote()
        campos = {"referencia": referencia, "link": link}
        if zerar_verificacao:
            campos.update(
                status="nao_verificada", julgada_pelo_professor=False, anotacao_correcao=None, data_verificacao=None
            )
            _apagar_trechos(loja, lote, fonte_id)
        lote.atualizar("fontes", fonte_id, campos)
        lote.confirmar()

    def adicionar_trecho(self, trecho):
        loja = armazenamento.loja()
        trecho.id = loja.novo_id()
        loja.criar("trechos", trecho.id, trecho.para_dict())
        return trecho

    def listar_trechos(self, fonte_id):
        docs = armazenamento.loja().consultar("trechos", fonte_id=fonte_id)
        return sorted((Trecho.de_dict(d) for d in docs), key=chave_id)
