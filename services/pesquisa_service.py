from repository.models import Pesquisa, Relatorio
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
        # status 'em_andamento' e a data de criação vêm do próprio model/banco.
        # RF20/RF22: o relatório nasce junto, ligado só a esta pesquisa (mesmo commit).
        pesquisa = Pesquisa(
            titulo=titulo, objetivo=objetivo, aluno_id=aluno.id, relatorio=Relatorio()
        )
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

    def concluir(self, pesquisa_id):  # RF10
        """Conclui a pesquisa: ela passa a 'concluida' (não muda mais) e o relatório é gerado
        e fica disponível para o professor. Fontes ainda não verificadas não impedem a
        conclusão; a tela avisa o aluno antes."""
        pesquisa = self.obter(pesquisa_id)  # exige aluno logado e dono da pesquisa
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída.")
        return self.repo.concluir(pesquisa.id)

    def excluir(self, pesquisa_id):  # RF09
        """Apaga uma pesquisa não concluída, com interações, fontes, trechos e o relatório dela.
        Pesquisa concluída já foi entregue ao professor e não pode ser apagada. A confirmação
        com o usuário é feita pela tela antes de chamar este método."""
        pesquisa = self.obter(pesquisa_id)  # exige aluno logado e dono da pesquisa
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída e entregue ao professor: não pode ser excluída.")
        self.repo.excluir(pesquisa.id)

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