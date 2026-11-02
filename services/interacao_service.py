from repository.interacao_repository import InteracaoRepository
from repository.models import Interacao
from services.erros import RegraViolada
from services.pesquisa_service import PesquisaService


class InteracaoService:
    def __init__(self):
        self.repo = InteracaoRepository()
        self.pesquisas = PesquisaService()

    def registrar(self, pesquisa_id, ferramenta_ia, pergunta, resposta):
        pesquisa = self.pesquisas.obter(pesquisa_id)
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída e não aceita novas interações.")

        ferramenta_ia = (ferramenta_ia or "").strip()
        pergunta = (pergunta or "").strip()
        resposta = (resposta or "").strip()
        if not ferramenta_ia:
            raise RegraViolada("Informe a ferramenta de IA usada.")
        if not pergunta:
            raise RegraViolada("Informe a pergunta feita à IA.")
        if not resposta:
            raise RegraViolada("Informe a resposta da IA.")

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
