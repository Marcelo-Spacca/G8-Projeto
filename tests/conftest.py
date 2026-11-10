"""Configuração dos testes.

IMPORTANTE: os testes APAGAM os dados do banco que usam. Por isso eles nunca usam o banco de
desenvolvimento (DB_NAME do .env): usam um banco separado, 'projeto1_teste' por padrão (ou o
valor de DB_NAME_TESTE no .env). Se o banco de teste ainda não existir, ele é criado aqui.
"""
import os

import pytest
from dotenv import load_dotenv

# 1) Troca o nome do banco ANTES de qualquer import do repository.
load_dotenv()
os.environ["DB_NAME"] = os.getenv("DB_NAME_TESTE", "projeto1_teste")

from sqlalchemy import create_engine, text  # noqa: E402

from repository.database import Base, engine, url  # noqa: E402
import repository.models  # noqa: E402,F401
from services.fonte_service import FonteService  # noqa: E402
from services.interacao_service import InteracaoService  # noqa: E402
from services.pesquisa_service import PesquisaService  # noqa: E402
from services.relatorio_service import RelatorioService  # noqa: E402
from services.sessao import sessao  # noqa: E402
from services.usuario_service import UsuarioService  # noqa: E402


def _criar_banco_se_nao_existe():
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conexao:
            existe = conexao.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :nome"), {"nome": url.database}
            ).scalar()
            if not existe:
                conexao.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def banco_de_teste():
    # Trava de segurança: nunca apagar um banco que não seja claramente de teste.
    assert url.database.endswith("_teste"), (
        f"O banco de testes precisa terminar com '_teste' (veio '{url.database}'). "
        "Ajuste DB_NAME_TESTE no .env."
    )
    _criar_banco_se_nao_existe()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def banco_limpo(banco_de_teste):
    """Cada teste começa com as tabelas vazias e ninguém logado."""
    tabelas = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conexao:
        conexao.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
    sessao.encerrar()
    yield
    sessao.encerrar()


@pytest.fixture
def usuarios():
    return UsuarioService()


@pytest.fixture
def pesquisas():
    return PesquisaService()


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
def entrar_como(usuarios):
    """Cadastra (se preciso) e loga um usuário. Ex.: entrar_como('bia@x.com', nome='Bia')."""

    def _entrar(email="ana@x.com", tipo="aluno", nome="Ana", senha="segredo1"):
        if usuarios.repo.buscar_por_email(email) is None:
            usuarios.cadastrar(nome, email, senha, tipo)
        return usuarios.entrar(email, senha)

    return _entrar
