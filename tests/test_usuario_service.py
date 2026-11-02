import pytest
from sqlalchemy import select

from repository.database import Session
from repository.models import Usuario
from services.erros import RegraViolada
from services.sessao import sessao


# ---------------------------------------------------------------- RF01
def test_cadastro_guarda_hash_e_normaliza_email(usuarios):
    u = usuarios.cadastrar("  Ana  ", "  ANA@X.com ", "segredo1", "aluno")
    assert u.id and u.nome == "Ana" and u.email == "ana@x.com" and u.tipo == "aluno"
    assert "segredo1" not in u.senha_hash
    with Session() as s:
        assert s.scalar(select(Usuario.senha_hash)) == u.senha_hash


@pytest.mark.parametrize(
    "nome,email,senha,tipo,trecho_da_mensagem",
    [
        ("", "a@x.com", "123456", "aluno", "nome"),
        ("A", "sem-arroba", "123456", "aluno", "e-mail"),
        ("A", "a@x.com", "123", "aluno", "senha"),
        ("A", "a@x.com", "123456", "admin", "perfil"),
        ("A", "a@x.com", "123456", "", "perfil"),
    ],
)
def test_cadastro_validacoes(usuarios, nome, email, senha, tipo, trecho_da_mensagem):
    with pytest.raises(RegraViolada, match=trecho_da_mensagem):
        usuarios.cadastrar(nome, email, senha, tipo)


def test_email_repetido_recusado_ate_com_caixa_diferente(usuarios):
    usuarios.cadastrar("A", "a@x.com", "123456", "aluno")
    with pytest.raises(RegraViolada, match="xiste uma conta"):
        usuarios.cadastrar("B", "A@X.COM", "abcdef", "professor")


def test_professor_pode_se_cadastrar(usuarios):
    assert usuarios.cadastrar("Prof", "p@x.com", "123456", "professor").tipo == "professor"


# ---------------------------------------------------------------- RF02
def test_login_com_sucesso_inicia_a_sessao(usuarios):
    usuarios.cadastrar("Ana", "ana@x.com", "segredo1", "aluno")
    u = usuarios.entrar(" ANA@x.com ", "segredo1")
    assert sessao.logado and sessao.usuario.id == u.id and u.nome == "Ana"


def test_login_errado_nao_inicia_a_sessao(usuarios):
    usuarios.cadastrar("Ana", "ana@x.com", "segredo1", "aluno")
    with pytest.raises(RegraViolada, match="incorretos"):
        usuarios.entrar("ana@x.com", "errada")
    with pytest.raises(RegraViolada, match="incorretos"):
        usuarios.entrar("nao@x.com", "segredo1")
    assert not sessao.logado


def test_logout_encerra_a_sessao(usuarios, entrar_como):
    entrar_como()
    assert sessao.logado
    usuarios.sair()
    assert not sessao.logado
