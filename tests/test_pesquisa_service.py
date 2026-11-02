import pytest

from services.erros import RegraViolada


# ---------------------------------------------------------------- RF06
def test_criar_pesquisa(pesquisas, entrar_como):
    aluno = entrar_como()
    p = pesquisas.criar("  Tema  ", " Objetivo ")
    assert p.status == "em_andamento" and p.aluno_id == aluno.id
    assert p.titulo == "Tema" and p.objetivo == "Objetivo" and p.data_criacao is not None


def test_criar_pesquisa_exige_titulo_e_objetivo(pesquisas, entrar_como):
    entrar_como()
    with pytest.raises(RegraViolada, match="título"):
        pesquisas.criar("   ", "O")
    with pytest.raises(RegraViolada, match="objetivo"):
        pesquisas.criar("T", "")


def test_criar_pesquisa_exige_login(pesquisas):
    with pytest.raises(RegraViolada, match="Entre"):
        pesquisas.criar("T", "O")


def test_professor_nao_cria_pesquisa(pesquisas, entrar_como):
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    with pytest.raises(RegraViolada, match="alunos"):
        pesquisas.criar("T", "O")


# ---------------------------------------------------------------- RF07
def test_listar_minhas_mais_recente_primeiro(pesquisas, entrar_como):
    entrar_como()
    pesquisas.criar("Tema", "Obj")
    pesquisas.criar("Segunda", "Obj")
    assert [p.titulo for p in pesquisas.listar_minhas()] == ["Segunda", "Tema"]


def test_listar_minhas_so_mostra_as_do_aluno_logado(pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    pesquisas.criar("Da Ana", "O")
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    assert pesquisas.listar_minhas() == []
    pesquisas.criar("Da Bia", "O")
    assert [p.titulo for p in pesquisas.listar_minhas()] == ["Da Bia"]


def test_listar_minhas_exige_aluno_logado(pesquisas, entrar_como):
    with pytest.raises(RegraViolada, match="Entre"):
        pesquisas.listar_minhas()
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    with pytest.raises(RegraViolada, match="alunos"):
        pesquisas.listar_minhas()


def test_obter_pesquisa_de_outro_aluno_e_como_inexistente(pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    p = pesquisas.criar("Da Ana", "O")
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        pesquisas.obter(p.id)
    with pytest.raises(RegraViolada, match="não encontrada"):
        pesquisas.obter(99999)
