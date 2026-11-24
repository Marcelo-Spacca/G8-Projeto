from repository.models import Pesquisa, Relatorio
from repository.pesquisa_repository import PesquisaRepository
from repository.turma_repository import TurmaRepository
from services.erros import RegraViolada
from services.sessao import sessao


def exigir_aluno():
    """Devolve o aluno logado ou levanta RegraViolada."""
    if not sessao.logado:
        raise RegraViolada("Entre na sua conta para continuar.")
    if sessao.usuario.tipo != "aluno":
        raise RegraViolada("Esta ação é exclusiva de alunos.")
    return sessao.usuario


def motivo_de_bloqueio(pesquisa):
    """Por que o aluno não pode mexer nesta pesquisa (None se pode)."""
    if pesquisa.status == "entregue":
        return "Esta pesquisa foi entregue ao professor e está em revisão: ela só volta a ser editada se ele devolver."
    if pesquisa.status == "concluida":
        return "Esta pesquisa já foi concluída pelo professor e não pode mais ser alterada."
    return None


class PesquisaService:
    def __init__(self):
        self.repo = PesquisaRepository()
        self.turmas = TurmaRepository()

    def criar(self, turma_id, titulo, objetivo):
        """Cria uma pesquisa individual do aluno logado, ligada a uma turma (cadeira) dele."""
        aluno = exigir_aluno()
        if not self.turmas.aluno_esta_na_turma(turma_id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        titulo = (titulo or "").strip()
        objetivo = (objetivo or "").strip()
        if not titulo:
            raise RegraViolada("Informe o título da pesquisa.")
        if not objetivo:
            raise RegraViolada("Informe o objetivo da pesquisa.")
        # status 'em_andamento' e a data de criação vêm do próprio model/banco.
        # RF20/RF22: o relatório nasce junto, ligado só a esta pesquisa (mesmo commit).
        pesquisa = Pesquisa(
            titulo=titulo, objetivo=objetivo, aluno_id=aluno.id, turma_id=turma_id, relatorio=Relatorio()
        )
        return self.repo.salvar(pesquisa)

    def editar(self, pesquisa_id, titulo, objetivo):  # RF08
        pesquisa = self.obter(pesquisa_id)  # exige aluno logado e dono da pesquisa
        if motivo_de_bloqueio(pesquisa):
            raise RegraViolada(motivo_de_bloqueio(pesquisa))
        titulo = (titulo or "").strip()
        objetivo = (objetivo or "").strip()
        if not titulo:
            raise RegraViolada("Informe o título da pesquisa.")
        if not objetivo:
            raise RegraViolada("Informe o objetivo da pesquisa.")
        return self.repo.atualizar(pesquisa.id, titulo, objetivo)

    def entregar(self, pesquisa_id):  # RF10
        """O aluno entrega a pesquisa ao professor. Ele passa a revisá-la e o aluno não pode mais
        alterar nada até o professor aceitar (concluída) ou devolver (volta a em andamento).
        Fontes ainda não verificadas não impedem a entrega; a tela avisa o aluno antes."""
        pesquisa = self.obter(pesquisa_id)  # exige aluno logado e dono da pesquisa
        if pesquisa.status == "entregue":
            raise RegraViolada("Esta pesquisa já foi entregue ao professor.")
        if pesquisa.status == "concluida":
            raise RegraViolada("Esta pesquisa já foi concluída pelo professor.")
        return self.repo.entregar(pesquisa.id)

    def excluir(self, pesquisa_id):  # RF09
        """Apaga uma pesquisa que ainda está com o aluno (em andamento), com interações, fontes,
        trechos e o relatório dela. Depois de entregue ao professor ela não pode ser apagada.
        A confirmação com o usuário é feita pela tela antes de chamar este método."""
        pesquisa = self.obter(pesquisa_id)  # exige aluno logado e dono da pesquisa
        if pesquisa.de_grupo:
            raise RegraViolada("Pesquisas de grupo não podem ser excluídas pelos alunos.")
        if pesquisa.status != "em_andamento":
            raise RegraViolada("Esta pesquisa foi entregue ao professor e não pode ser excluída.")
        self.repo.excluir(pesquisa.id)

    def listar_minhas(self, turma_id):
        """Pesquisas individuais do aluno na turma."""
        aluno = exigir_aluno()
        if not self.turmas.aluno_esta_na_turma(turma_id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        return self.repo.listar_por_aluno(aluno.id, turma_id)

    def listar_de_grupo(self, turma_id):
        """Pesquisas dos grupos de que o aluno participa na turma."""
        aluno = exigir_aluno()
        if not self.turmas.aluno_esta_na_turma(turma_id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        return self.repo.listar_de_grupos_do_aluno(aluno.id, turma_id)

    def obter(self, pesquisa_id):
        """A pesquisa do aluno logado ou do grupo de que ele faz parte."""
        aluno = exigir_aluno()
        # Pesquisa de outro aluno (ou de grupo alheio) é tratada como inexistente.
        if not self.repo.aluno_acessa(pesquisa_id, aluno.id):
            raise RegraViolada("Pesquisa não encontrada.")
        return self.repo.buscar_por_id(pesquisa_id)
