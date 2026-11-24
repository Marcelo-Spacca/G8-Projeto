"""Grupos dentro de uma turma: uma única pesquisa feita por vários alunos.

Fluxo: um aluno cria o grupo (nome, título e objetivo) e convida colegas da turma. Quando o primeiro
convite é aceito, nasce a pesquisa do grupo; ela pertence ao grupo, não a um aluno. O professor
também pode atribuir alunos a um grupo e removê-los. Só existe se a turma permitir grupos.
"""
from repository.grupo_repository import GrupoRepository
from repository.turma_repository import TurmaRepository
from services.erros import RegraViolada
from services.pesquisa_service import exigir_aluno
from services.relatorio_service import exigir_professor


def _limpar(texto):
    return (texto or "").strip()


def _exigir_pesquisa_do_grupo_com_o_aluno(grupo):
    """Os integrantes só mudam enquanto a pesquisa do grupo está com os alunos."""
    pesquisa = grupo.pesquisa
    if pesquisa is None or pesquisa.status == "em_andamento":
        return
    if pesquisa.status == "entregue":
        raise RegraViolada(
            "A pesquisa deste grupo foi entregue ao professor: os integrantes só podem mudar se ela for devolvida."
        )
    raise RegraViolada("A pesquisa deste grupo já foi concluída: os integrantes não podem mais mudar.")


class GrupoService:
    def __init__(self):
        self.repo = GrupoRepository()
        self.turmas = TurmaRepository()

    # ---------------------------------------------------------------- aluno
    def _turma_com_grupos(self, turma_id, aluno):
        turma = self.turmas.buscar_por_id(turma_id)
        if turma is None or not self.turmas.aluno_esta_na_turma(turma.id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        if not turma.permite_grupos:
            raise RegraViolada("Esta turma não permite grupos.")
        return turma

    def criar(self, turma_id, nome, titulo, objetivo):
        """Cria um grupo na turma, com o aluno logado como primeiro integrante. A pesquisa do grupo
        só nasce quando outro aluno aceitar o convite."""
        aluno = exigir_aluno()
        turma = self._turma_com_grupos(turma_id, aluno)
        nome, titulo, objetivo = _limpar(nome), _limpar(titulo), _limpar(objetivo)
        if not nome:
            raise RegraViolada("Dê um nome ao grupo.")
        if not titulo:
            raise RegraViolada("Informe o título da pesquisa do grupo.")
        if not objetivo:
            raise RegraViolada("Informe o objetivo da pesquisa do grupo.")
        grupo_id = self.repo.criar(turma.id, aluno.id, nome, titulo, objetivo)
        return self.repo.buscar_por_id(grupo_id)

    def obter(self, grupo_id):
        """Grupo de que o aluno logado faz parte (qualquer outro é tratado como inexistente)."""
        aluno = exigir_aluno()
        if not self.repo.aluno_e_integrante(grupo_id, aluno.id):
            raise RegraViolada("Grupo não encontrado.")
        return self.repo.buscar_por_id(grupo_id)

    def listar_do_aluno(self, turma_id):
        """Os grupos da turma de que o aluno participa, com integrantes e pesquisa."""
        aluno = exigir_aluno()
        turma = self.turmas.buscar_por_id(turma_id)
        if turma is None or not self.turmas.aluno_esta_na_turma(turma.id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        return self.repo.listar_do_aluno(aluno.id, turma.id)

    def convidaveis(self, grupo_id):
        """Colegas da turma que ainda podem ser convidados: fora do grupo e sem convite pendente."""
        grupo = self.obter(grupo_id)
        ocupados = {m.aluno_id for m in grupo.membros}
        ocupados |= {c.aluno_id for c in grupo.convites if c.status == "pendente"}
        return [a for a in self.turmas.listar_alunos(grupo.turma_id) if a.id not in ocupados]

    def convidar(self, grupo_id, alunos_ids):
        """Um integrante convida colegas da turma para o grupo."""
        aluno = exigir_aluno()
        grupo = self.obter(grupo_id)
        self._turma_com_grupos(grupo.turma_id, aluno)
        _exigir_pesquisa_do_grupo_com_o_aluno(grupo)
        alunos_ids = list(dict.fromkeys(alunos_ids or []))
        if not alunos_ids:
            raise RegraViolada("Escolha pelo menos um colega para convidar.")
        validos = {a.id for a in self.convidaveis(grupo_id)}
        for aluno_id in alunos_ids:
            if aluno_id not in validos:
                raise RegraViolada(
                    "Só é possível convidar alunos desta turma que ainda não estão no grupo e não têm convite pendente."
                )
        self.repo.convidar(grupo.id, alunos_ids, aluno.id)
        return len(alunos_ids)

    def convites_pendentes(self, turma_id):
        """Convites que o aluno logado recebeu nesta turma e ainda não respondeu."""
        aluno = exigir_aluno()
        turma = self.turmas.buscar_por_id(turma_id)
        if turma is None or not self.turmas.aluno_esta_na_turma(turma.id, aluno.id):
            raise RegraViolada("Turma não encontrada.")
        if not turma.permite_grupos:
            return []
        return self.repo.convites_pendentes(aluno.id, turma.id)

    def responder_convite(self, convite_id, aceitar):
        """Aceitar coloca o aluno no grupo (e cria a pesquisa do grupo, se ainda não existe);
        recusar só encerra o convite."""
        aluno = exigir_aluno()
        convite = self.repo.buscar_convite(convite_id)
        if convite is None or convite.aluno_id != aluno.id:
            raise RegraViolada("Convite não encontrado.")
        if convite.status != "pendente":
            raise RegraViolada("Este convite já foi respondido.")
        if aceitar:
            grupo = self.repo.buscar_por_id(convite.grupo_id)
            _exigir_pesquisa_do_grupo_com_o_aluno(grupo)
        self.repo.responder_convite(convite.id, bool(aceitar))
        return self.repo.buscar_por_id(convite.grupo_id)

    # ---------------------------------------------------------------- professor
    def _grupo_do_professor(self, grupo_id):
        professor = exigir_professor()
        grupo = self.repo.buscar_por_id(grupo_id)
        if grupo is None or grupo.turma.professor_id != professor.id:
            raise RegraViolada("Grupo não encontrado.")
        return grupo

    def atribuir_aluno(self, grupo_id, aluno_id):
        """O professor coloca um aluno da turma num grupo."""
        grupo = self._grupo_do_professor(grupo_id)
        _exigir_pesquisa_do_grupo_com_o_aluno(grupo)
        if not self.turmas.aluno_esta_na_turma(grupo.turma_id, aluno_id):
            raise RegraViolada("Este aluno não faz parte da turma.")
        if any(m.aluno_id == aluno_id for m in grupo.membros):
            raise RegraViolada("Este aluno já está no grupo.")
        self.repo.adicionar_integrante(grupo.id, aluno_id)
        return self.repo.buscar_por_id(grupo.id)

    def remover_aluno(self, grupo_id, aluno_id):
        """O professor tira um aluno do grupo. O último integrante não pode sair."""
        grupo = self._grupo_do_professor(grupo_id)
        _exigir_pesquisa_do_grupo_com_o_aluno(grupo)
        if not any(m.aluno_id == aluno_id for m in grupo.membros):
            raise RegraViolada("Este aluno não está no grupo.")
        if len(grupo.membros) <= 1:
            raise RegraViolada("O grupo precisa ter pelo menos um aluno: este é o último integrante.")
        self.repo.remover_integrante(grupo.id, aluno_id)
        return self.repo.buscar_por_id(grupo.id)
