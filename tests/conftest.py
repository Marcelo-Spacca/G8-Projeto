"""Configuração dos testes.

Os testes NÃO usam o Firebase: cada teste roda contra um MemoryStore novo (os dados ficam só na
memória), então não precisam de internet, de credenciais nem de banco instalado, e nunca mexem em
dados reais. Para conferir o FirestoreStore de verdade, veja tests/test_firestore_real.py.
"""
import pytest

from repository import armazenamento  # noqa: E402
from repository.armazenamento import MemoryStore  # noqa: E402
from repository.turma_repository import TurmaRepository  # noqa: E402
from repository.models import Turma, Usuario  # noqa: E402
from services.fonte_service import FonteService  # noqa: E402
from services.interacao_service import InteracaoService  # noqa: E402
from services.pesquisa_service import PesquisaService  # noqa: E402
from services.relatorio_service import RelatorioService  # noqa: E402
from services.revisao_service import RevisaoService  # noqa: E402
from services.sessao import sessao  # noqa: E402
from services.turma_service import TurmaService  # noqa: E402
from services.grupo_service import GrupoService  # noqa: E402
from services.usuario_service import UsuarioService  # noqa: E402

NOME_TURMA_PADRAO = "Turma padrão"


@pytest.fixture(autouse=True)
def banco_limpo():
    """Cada teste começa com dados vazios (um MemoryStore novo) e ninguém logado."""
    armazenamento.usar(MemoryStore())
    sessao.encerrar()
    yield
    sessao.encerrar()


@pytest.fixture
def usuarios():
    return UsuarioService()


class PesquisaServiceDeTeste(PesquisaService):
    """Os testes antigos criam pesquisa só com título e objetivo. Este service aceita isso e põe
    a pesquisa numa 'Turma padrão' (criada na hora, com o aluno matriculado). O professor que
    entra depois via 'entrar_como' passa a ser o dono dela, então ele enxerga essas pesquisas.
    O fluxo real, com o id da turma, é 'criar_na_turma' (o método original do service)."""

    criar_na_turma = PesquisaService.criar

    def _turma_padrao(self):
        """Id da 'Turma padrão' (criada se preciso), com o aluno logado matriculado nela."""
        aluno = sessao.usuario
        repo_turmas = TurmaRepository()
        achadas = [t for t in armazenamento.loja().consultar("turmas") if t["nome"] == NOME_TURMA_PADRAO]
        if achadas:
            turma_id = achadas[0]["id"]
        else:
            from repository.usuario_repository import UsuarioRepository

            donos = [d for d in armazenamento.loja().consultar("usuarios") if d["tipo"] == "professor"]
            if donos:
                dono_id = min(donos, key=lambda d: (len(d["id"]), d["id"]))["id"]
            else:
                dono_id = UsuarioRepository().salvar(
                    Usuario(nome="Dono padrão", email="dono-padrao@x.com", senha_hash="x", tipo="professor")
                ).id
            turma_id = repo_turmas.salvar(
                Turma(nome=NOME_TURMA_PADRAO, codigo="PADRAO", permite_grupos=True, professor_id=dono_id)
            ).id
        if aluno is not None and aluno.tipo == "aluno" and not repo_turmas.aluno_esta_na_turma(turma_id, aluno.id):
            repo_turmas.matricular(turma_id, aluno.id)
        return turma_id

    def criar(self, titulo, objetivo):
        return self.criar_na_turma(self._turma_padrao(), titulo, objetivo)

    def listar_minhas(self, turma_id=None):
        return super().listar_minhas(self._turma_padrao() if turma_id is None else turma_id)


@pytest.fixture
def pesquisas():
    return PesquisaServiceDeTeste()


@pytest.fixture
def turmas():
    return TurmaService()


@pytest.fixture
def grupos():
    return GrupoService()


@pytest.fixture
def interacoes():
    return InteracaoService()


@pytest.fixture
def fontes():
    return FonteService()


@pytest.fixture
def relatorios():
    return RelatorioService()


@pytest.fixture
def revisoes():
    return RevisaoService()


@pytest.fixture
def entrar_como(usuarios):
    """Cadastra (se preciso) e loga um usuário. Ex.: entrar_como('bia@x.com', nome='Bia')."""

    def _entrar(email="ana@x.com", tipo="aluno", nome="Ana", senha="segredo1"):
        if usuarios.repo.buscar_por_email(email) is None:
            usuarios.cadastrar(nome, email, senha, tipo)
        usuario = usuarios.entrar(email, senha)
        if tipo == "professor":  # a 'Turma padrão' dos testes antigos passa a ser deste professor
            for turma in armazenamento.loja().consultar("turmas", nome=NOME_TURMA_PADRAO):
                armazenamento.loja().atualizar("turmas", turma["id"], {"professor_id": usuario.id})
        return usuario

    return _entrar
