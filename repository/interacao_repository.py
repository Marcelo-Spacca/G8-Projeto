from repository import armazenamento
from repository.armazenamento import agora
from repository.carga import carregar_interacoes
from repository.cascata import apagar_interacoes
from repository.models import Interacao


class InteracaoRepository:
    def salvar(self, interacao):
        loja = armazenamento.loja()
        interacao.id = loja.novo_id()
        loja.criar("interacoes", interacao.id, interacao.para_dict())
        return interacao

    def listar_por_pesquisa(self, pesquisa_id):
        """Interações da pesquisa, em ordem de registro, com as fontes (a tela mostra
        "2 fontes, 1 pendente")."""
        docs = armazenamento.loja().consultar("interacoes", pesquisa_id=pesquisa_id)
        from repository.carga import chave_id

        return sorted(carregar_interacoes(docs, fontes=True), key=lambda i: (i.data_registro, chave_id(i)))

    def buscar_por_id(self, interacao_id):
        """Interação já com as fontes e os trechos de cada fonte (para a tela da interação)."""
        doc = armazenamento.loja().obter("interacoes", interacao_id)
        return carregar_interacoes([doc], fontes=True, trechos=True)[0] if doc else None

    def atualizar(self, interacao_id, ferramenta_ia, pergunta, resposta):
        """RF13: muda só os textos; as fontes ligadas continuam as mesmas."""
        loja = armazenamento.loja()
        loja.atualizar(
            "interacoes", interacao_id, {"ferramenta_ia": ferramenta_ia, "pergunta": pergunta, "resposta": resposta}
        )
        return Interacao.de_dict(loja.obter("interacoes", interacao_id))

    def registrar_comentario(self, interacao_id, comentario):
        """Comentário do professor (vazio apaga o comentário)."""
        armazenamento.loja().atualizar(
            "interacoes",
            interacao_id,
            {"comentario_professor": comentario, "data_comentario": agora() if comentario else None},
        )

    def definir_confirmada(self, interacao_id, confirmada):
        armazenamento.loja().atualizar("interacoes", interacao_id, {"confirmada": confirmada})

    def excluir(self, interacao_id):
        """RF14: apaga junto as fontes e os trechos."""
        loja = armazenamento.loja()
        lote = loja.lote()
        apagar_interacoes(loja, lote, [interacao_id])
        lote.confirmar()
