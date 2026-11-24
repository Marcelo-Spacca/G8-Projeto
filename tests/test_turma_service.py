"""Turmas: o professor cria (com código), o aluno entra pelo código e cria as pesquisas dentro dela."""
import pytest

from services.erros import RegraViolada
from services.sessao import sessao
from services.turma_service import ALFABETO_CODIGO, TAMANHO_CODIGO


@pytest.fixture
def como(entrar_como):
    def _como(email, tipo="aluno", nome=None):
        sessao.encerrar()
        return entrar_como(email, tipo=tipo, nome=nome or email.split("@")[0].title())

    return _como


@pytest.fixture
def turma(como, turmas):
    como("prof@x.com", "professor")
    return turmas.criar("Cálculo I")


# ---------------------------------------------------------------- criar e código
def test_professor_cria_turma_com_codigo_de_entrada(turmas, como):
    como("prof@x.com", "professor")
    t = turmas.criar("  Cálculo I  ", permite_grupos=True)
    assert t.nome == "Cálculo I" and t.permite_grupos is True
    assert len(t.codigo) == TAMANHO_CODIGO and set(t.codigo) <= set(ALFABETO_CODIGO)
    assert t.professor_id == sessao.usuario.id


def test_turma_nasce_sem_grupos_e_com_codigos_diferentes(turmas, como):
    como("prof@x.com", "professor")
    codigos = {turmas.criar(f"T{i}").codigo for i in range(15)}
    assert len(codigos) == 15
    assert turmas.criar("Outra").permite_grupos is False


def test_turma_exige_nome(turmas, como):
    como("prof@x.com", "professor")
    with pytest.raises(RegraViolada, match="nome da turma"):
        turmas.criar("   ")


def test_so_professor_cria_turma(turmas, como):
    como("ana@x.com")
    with pytest.raises(RegraViolada, match="exclusiva de professores"):
        turmas.criar("Cálculo")


# ---------------------------------------------------------------- aluno entra pelo código
def test_aluno_entra_digitando_o_codigo(turmas, como, turma):
    como("ana@x.com")
    entrou = turmas.entrar(f"  {turma.codigo.lower()[:3]} {turma.codigo.lower()[3:]} ")  # minúsculas e espaços
    assert entrou.id == turma.id
    assert [t.id for t in turmas.listar_do_aluno()] == [turma.id]
    assert turmas.obter_do_aluno(turma.id).professor.nome == "Prof"


def test_codigo_invalido_vazio_ou_repetido(turmas, como, turma):
    como("ana@x.com")
    with pytest.raises(RegraViolada, match="Não existe turma"):
        turmas.entrar("ZZZZZZ")
    with pytest.raises(RegraViolada, match="Digite o código"):
        turmas.entrar("  ")
    turmas.entrar(turma.codigo)
    with pytest.raises(RegraViolada, match="já está nesta turma"):
        turmas.entrar(turma.codigo)


def test_professor_nao_entra_em_turma(turmas, turma):
    with pytest.raises(RegraViolada, match="exclusiva de alunos"):
        turmas.entrar(turma.codigo)


def test_aluno_entra_em_varias_turmas_e_so_ve_as_suas(turmas, como):
    como("prof@x.com", "professor")
    a, b, c = turmas.criar("A"), turmas.criar("B"), turmas.criar("C")
    como("ana@x.com")
    turmas.entrar(a.codigo)
    turmas.entrar(b.codigo)
    assert {t.nome for t in turmas.listar_do_aluno()} == {"A", "B"}
    with pytest.raises(RegraViolada, match="Turma não encontrada"):
        turmas.obter_do_aluno(c.id)
    como("bia@x.com")
    assert turmas.listar_do_aluno() == []


def test_colegas_sao_os_outros_alunos_da_turma(turmas, como, turma):
    for email in ("ana@x.com", "bia@x.com", "caio@x.com"):
        como(email)
        turmas.entrar(turma.codigo)
    como("dani@x.com")  # fora da turma
    como("ana@x.com")
    assert [a.nome for a in turmas.colegas(turma.id)] == ["Bia", "Caio"]


# ---------------------------------------------------------------- pesquisa dentro da turma
def test_aluno_so_cria_pesquisa_na_turma_em_que_entrou(turmas, pesquisas, como, turma):
    como("ana@x.com")
    with pytest.raises(RegraViolada, match="Turma não encontrada"):
        pesquisas.criar_na_turma(turma.id, "Tema", "Objetivo")
    turmas.entrar(turma.codigo)
    p = pesquisas.criar_na_turma(turma.id, "Tema", "Objetivo")
    assert p.turma_id == turma.id and p.aluno_id == sessao.usuario.id and p.grupo_id is None


def test_pesquisas_ficam_separadas_por_turma(turmas, pesquisas, como):
    como("prof@x.com", "professor")
    a, b = turmas.criar("A"), turmas.criar("B")
    como("ana@x.com")
    turmas.entrar(a.codigo)
    turmas.entrar(b.codigo)
    pesquisas.criar_na_turma(a.id, "Da A", "o")
    pesquisas.criar_na_turma(b.id, "Da B 1", "o")
    pesquisas.criar_na_turma(b.id, "Da B 2", "o")
    assert [p.titulo for p in pesquisas.listar_minhas(a.id)] == ["Da A"]
    assert [p.titulo for p in pesquisas.listar_minhas(b.id)] == ["Da B 2", "Da B 1"]
    como("bia@x.com")
    with pytest.raises(RegraViolada, match="Turma não encontrada"):
        pesquisas.listar_minhas(a.id)


# ---------------------------------------------------------------- professor e suas turmas
def test_professor_so_ve_e_apaga_as_proprias_turmas(turmas, como, turma):
    como("outro@x.com", "professor")
    assert turmas.listar_do_professor() == []
    with pytest.raises(RegraViolada, match="Turma não encontrada"):
        turmas.obter_do_professor(turma.id)
    with pytest.raises(RegraViolada, match="Turma não encontrada"):
        turmas.excluir(turma.id)
    como("prof@x.com", "professor")
    assert [t.id for t in turmas.listar_do_professor()] == [turma.id]


def test_aluno_nao_usa_as_funcoes_do_professor(turmas, como, turma):
    como("ana@x.com")
    with pytest.raises(RegraViolada, match="exclusiva de professores"):
        turmas.listar_do_professor()
    with pytest.raises(RegraViolada, match="exclusiva de professores"):
        turmas.excluir(turma.id)
    with pytest.raises(RegraViolada, match="exclusiva de professores"):
        turmas.obter_do_professor(turma.id)


def test_professor_ve_alunos_e_suas_pesquisas_agrupados(turmas, pesquisas, como, turma):
    for email, titulos in (("bia@x.com", ["B1"]), ("ana@x.com", ["A1", "A2"]), ("caio@x.com", [])):
        como(email)
        turmas.entrar(turma.codigo)
        for t in titulos:
            pesquisas.criar_na_turma(turma.id, t, "o")
    como("prof@x.com", "professor")
    carregada = turmas.obter_do_professor(turma.id)
    assert [a.nome for a in carregada.alunos] == ["Ana", "Bia", "Caio"]
    por_aluno = {a.nome: sorted(p.titulo for p in carregada.pesquisas if p.aluno_id == a.id) for a in carregada.alunos}
    assert por_aluno == {"Ana": ["A1", "A2"], "Bia": ["B1"], "Caio": []}


def test_excluir_turma_apaga_pesquisas_e_matriculas(turmas, pesquisas, interacoes, como, turma):
    como("ana@x.com")
    turmas.entrar(turma.codigo)
    p = pesquisas.criar_na_turma(turma.id, "Tema", "o")
    interacoes.registrar(p.id, "IA", "q", "r")
    como("prof@x.com", "professor")
    turmas.excluir(turma.id)
    assert turmas.listar_do_professor() == []
    como("ana@x.com")
    assert turmas.listar_do_aluno() == []
    with pytest.raises(RegraViolada, match="Pesquisa não encontrada"):
        pesquisas.obter(p.id)
    # o código da turma apagada deixa de valer
    with pytest.raises(RegraViolada, match="Não existe turma"):
        turmas.entrar(turma.codigo)


# ---------------------------------------------------------------- o professor só alcança as próprias turmas
@pytest.fixture
def duas_turmas(turmas, pesquisas, como):
    como("prof@x.com", "professor")
    minha = turmas.criar("Minha")
    como("outro@x.com", "professor")
    alheia = turmas.criar("Alheia")
    como("ana@x.com")
    turmas.entrar(minha.codigo)
    turmas.entrar(alheia.codigo)
    p_minha = pesquisas.criar_na_turma(minha.id, "Na minha", "o")
    p_alheia = pesquisas.criar_na_turma(alheia.id, "Na alheia", "o")
    for p in (p_minha, p_alheia):
        pesquisas.entregar(p.id)
    como("prof@x.com", "professor")
    return minha, alheia, p_minha, p_alheia


def test_professor_lista_so_pesquisas_das_suas_turmas_e_filtra_por_turma(revisoes, turmas, pesquisas, como, duas_turmas):
    minha, alheia, p_minha, p_alheia = duas_turmas
    assert [p.titulo for p in revisoes.listar_todas()] == ["Na minha"]
    assert [p.titulo for p in revisoes.listar_todas(minha.id)] == ["Na minha"]
    assert revisoes.listar_todas(alheia.id) == []  # filtrar por turma alheia não revela nada


def test_filtro_por_turma_separa_as_pesquisas(turmas, pesquisas, revisoes, como):
    como("prof@x.com", "professor")
    a, b = turmas.criar("A"), turmas.criar("B")
    como("ana@x.com")
    turmas.entrar(a.codigo)
    turmas.entrar(b.codigo)
    pesquisas.criar_na_turma(a.id, "da A", "o")
    pesquisas.criar_na_turma(b.id, "da B", "o")
    como("prof@x.com", "professor")
    assert {p.titulo for p in revisoes.listar_todas()} == {"da A", "da B"}
    assert [p.titulo for p in revisoes.listar_todas(a.id)] == ["da A"]
    assert [p.titulo for p in revisoes.listar_todas(b.id)] == ["da B"]


def test_professor_nao_alcanca_pesquisa_de_turma_alheia(revisoes, relatorios, como, duas_turmas):
    _, _, p_minha, p_alheia = duas_turmas
    assert revisoes.obter_pesquisa(p_minha.id).titulo == "Na minha"
    assert relatorios.gerar(p_minha.id).pesquisa.titulo == "Na minha"
    for acao in (
        lambda: revisoes.obter_pesquisa(p_alheia.id),
        lambda: relatorios.gerar(p_alheia.id),
        lambda: revisoes.aceitar(p_alheia.id),
        lambda: revisoes.devolver(p_alheia.id, "volta"),
    ):
        with pytest.raises(RegraViolada, match="Pesquisa não encontrada"):
            acao()


def test_professor_nao_alcanca_interacao_nem_fonte_de_turma_alheia(revisoes, interacoes, fontes, como, turmas, pesquisas):
    como("outro@x.com", "professor")
    alheia = turmas.criar("Alheia")
    como("ana@x.com")
    turmas.entrar(alheia.codigo)
    p = pesquisas.criar_na_turma(alheia.id, "T", "o")
    i = interacoes.registrar(p.id, "IA", "q", "r")
    f = fontes.adicionar(i.id, "Ref")
    pesquisas.entregar(p.id)
    como("prof@x.com", "professor")
    with pytest.raises(RegraViolada, match="Interação não encontrada"):
        revisoes.obter_interacao(i.id)
    with pytest.raises(RegraViolada, match="não encontrada"):
        revisoes.julgar_fonte(f.id, "verificada")
    with pytest.raises(RegraViolada, match="não encontrada"):
        revisoes.comentar_interacao(i.id, "oi")
    with pytest.raises(RegraViolada, match="não encontrada"):
        revisoes.confirmar_interacao(i.id)
