"""Testes no PostgreSQL, num banco separado (padrão: projeto1_teste).

O banco é criado automaticamente se não existir; o usuário do .env precisa ter
permissão para criar bancos. O banco principal (DB_NAME) nunca é tocado.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

import repository.models  # noqa: F401  (registra os models em Base)
from repository.database import Base
from services.servicos import (
    FonteService,
    InteracaoService,
    PesquisaService,
    RelatorioService,
    UsuarioService,
)

load_dotenv()

NOME_BANCO_TESTE = os.getenv("DB_NAME_TESTE", "projeto1_teste")
if not NOME_BANCO_TESTE.endswith("_teste"):
    raise RuntimeError(
        f"DB_NAME_TESTE='{NOME_BANCO_TESTE}' precisa terminar com '_teste' (proteção do banco real)."
    )


def _url(banco: str) -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=banco,
    )


def _garantir_banco_teste() -> None:
    admin = create_engine(_url("postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as c:
            existe = c.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": NOME_BANCO_TESTE}
            )
            if not existe:
                c.execute(text(f'CREATE DATABASE "{NOME_BANCO_TESTE}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session")
def engine():
    _garantir_banco_teste()
    eng = create_engine(_url(NOME_BANCO_TESTE))
    Base.metadata.drop_all(eng)  # recria as tabelas para refletir os models atuais
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def sf(engine):
    """Cada teste começa com as tabelas vazias."""
    tabelas = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as c:
        c.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def svc(sf):
    class S:
        usuarios = UsuarioService(sf)
        pesquisas = PesquisaService(sf)
        interacoes = InteracaoService(sf)
        fontes = FonteService(sf)
        relatorios = RelatorioService(sf)

    return S


@pytest.fixture
def aluno(svc):
    return svc.usuarios.cadastrar("Ana", "ana@ex.com", "segredo1", "aluno")


@pytest.fixture
def professor(svc):
    return svc.usuarios.cadastrar("Prof", "prof@ex.com", "segredo1", "professor")


@pytest.fixture
def pesquisa(svc, aluno):
    return svc.pesquisas.criar(aluno.id, "Fotossíntese", "Entender a fase clara")


@pytest.fixture
def interacao(svc, aluno, pesquisa):
    return svc.interacoes.registrar(
        aluno.id, pesquisa.id, "ChatGPT", "O que é?", "É um processo...", ["Livro A", "Artigo B"]
    )


def contar(sf, model):
    with sf() as s:
        return s.scalar(select(func.count()).select_from(model))
