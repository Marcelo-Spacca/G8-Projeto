from repository.models import Pesquisa
from repository.pesquisa_repository import PesquisaRepository
from services.erros import RegraViolada
from services.sessao import sessao


def exigir_aluno():
    """Devolve o aluno logado ou levanta RegraViolada."""
    if not sessao.logado:
        raise RegraViolada("Entre na sua conta para continuar.")
    if sessao.usuario.tipo != "aluno":
        raise RegraViolada("Esta ação é exclusiva de alunos.")
    return sessao.usuario


class PesquisaService:
    def __init__(self):
        self.repo = PesquisaRepository()

    def criar(self, titulo, objetivo):
        aluno = exigir_aluno()
        titulo = (titulo or "").strip()
        objetivo = (objetivo or "").strip()
        if not titulo:
            raise RegraViolada("Informe o título da pesquisa.")
        if not objetivo:
            raise RegraViolada("Informe o objetivo da pesquisa.")
        # status 'em_andamento' e a data de criação vêm do próprio model/banco
        pesquisa = Pesquisa(titulo=titulo, objetivo=objetivo, aluno_id=aluno.id)
        return self.repo.salvar(pesquisa)

    def editar(self, pesquisa_id, titulo, objetivo):  # RF08
        pesquisa = self.obter(pesquisa_id)  # exige aluno logado e dono da pesquisa
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída e não pode ser editada.")
        titulo = (titulo or "").strip()
        objetivo = (objetivo or "").strip()
        if not titulo:
            raise RegraViolada("Informe o título da pesquisa.")
        if not objetivo:
            raise RegraViolada("Informe o objetivo da pesquisa.")
        return self.repo.atualizar(pesquisa.id, titulo, objetivo)

    def listar_minhas(self):
        aluno = exigir_aluno()
        return self.repo.listar_por_aluno(aluno.id)

    def obter(self, pesquisa_id):
        aluno = exigir_aluno()
        pesquisa = self.repo.buscar_por_id(pesquisa_id)
        # Pesquisa de outro aluno é tratada como inexistente.
        if pesquisa is None or pesquisa.aluno_id != aluno.id:
            raise RegraViolada("Pesquisa não encontrada.")
        return pesquisa