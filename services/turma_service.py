"""Turmas (RF04/RF05): o professor cria a turma, que ganha um código de entrada; o aluno entra
digitando o código e, dentro da turma, cria as pesquisas da cadeira."""
import secrets

from repository.models import Turma
from repository.turma_repository import TurmaRepository
from services.erros import RegraViolada
from services.pesquisa_service import exigir_aluno
from services.relatorio_service import exigir_professor

# sem 0/O, 1/I/L: o código é digitado à mão, então evitamos letras que se confundem
ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
TAMANHO_CODIGO = 6


def normalizar_codigo(codigo):
    return "".join((codigo or "").split()).upper().replace("-", "")


class TurmaService:
    def __init__(self):
        self.repo = TurmaRepository()

    def _novo_codigo(self):
        while True:
            codigo = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(TAMANHO_CODIGO))
            if not self.repo.codigo_existe(codigo):
                return codigo

    # ---------------------------------------------------------------- professor
    def criar(self, nome, permite_grupos=False):
        """Cria a turma do professor logado e gera o código de entrada."""
        professor = exigir_professor()
        nome = (nome or "").strip()
        if not nome:
            raise RegraViolada("Informe o nome da turma.")
        turma = Turma(
            nome=nome,
            codigo=self._novo_codigo(),
            permite_grupos=bool(permite_grupos),
            professor_id=professor.id,
        )
        return self.repo.salvar(turma)

    def listar_do_professor(self):
        professor = exigir_professor()
        return self.repo.listar_do_professor(professor.id)

    def _turma_do_professor(self, turma_id):
        professor = exigir_professor()
        turma = self.repo.buscar_por_id(turma_id)
        # turma de outro professor é tratada como inexistente
        if turma is None or turma.professor_id != professor.id:
            raise RegraViolada("Turma não encontrada.")
        return turma

    def obter_do_professor(self, turma_id):
        """A turma com alunos, grupos e pesquisas carregados."""
        turma = self._turma_do_professor(turma_id)
        return self.repo.carregar_completa(turma.id)

    def excluir(self, turma_id):
        """Apaga a turma e tudo o que há nela (matrículas, grupos, pesquisas, interações, fontes).
        A confirmação com o usuário é feita pela tela antes de chamar este método."""
        turma = self._turma_do_professor(turma_id)
        self.repo.excluir(turma.id)

    # ---------------------------------------------------------------- aluno
    def entrar(self, codigo):
        """O aluno entra numa turma digitando o código que o professor passou."""
        aluno = exigir_aluno()
        codigo = normalizar_codigo(codigo)
        if not codigo:
            raise RegraViolada("Digite o código da turma.")
        turma = self.repo.buscar_por_codigo(codigo)
        if turma is None:
            raise RegraViolada("Não existe turma com esse código. Confira com o professor.")
        if self.repo.aluno_esta_na_turma(turma.id, aluno.id):
            raise RegraViolada("Você já está nesta turma.")
        self.repo.matricular(turma.id, aluno.id)
        return turma

    def listar_do_aluno(self):
        aluno = exigir_aluno()
        return self.repo.listar_do_aluno(aluno.id)

    def obter_do_aluno(self, turma_id):
        """A turma, se o aluno logado faz parte dela. Qualquer outra é tratada como inexistente."""
        aluno = exigir_aluno()
        turma = self.repo.buscar_por_id(turma_id)
        if turma is None or not self.repo.aluno_esta_na_turma(turma.id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        return turma

    def colegas(self, turma_id):
        """Os outros alunos da turma (para convidar para um grupo)."""
        aluno = exigir_aluno()
        turma = self.obter_do_aluno(turma_id)
        return [a for a in self.repo.listar_alunos(turma.id) if a.id != aluno.id]
