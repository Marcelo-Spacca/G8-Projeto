import pytest

from services.erros import RegraViolada


@pytest.fixture
def interacao(interacoes, pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    return interacoes.registrar(p.id, "ChatGPT", "pergunta", "resposta")


def test_adicionar_fonte_nasce_nao_verificada(fontes, interacao):
    f = fontes.adicionar(interacao.id, "  Silva (2023)  ")
    assert f.referencia == "Silva (2023)" and f.status == "nao_verificada"


def test_adicionar_fonte_exige_referencia(fontes, interacao):
    with pytest.raises(RegraViolada, match="referência"):
        fontes.adicionar(interacao.id, "   ")


# ---------------------------------------------------------------- RF26
def test_verificar_com_trecho_salva_o_trecho_junto_da_fonte(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    v = fontes.verificar(f.id, "verificada", trecho="  A IA mudou o ensino.  ", localizacao=" §2 ")
    assert v.status == "verificada" and v.data_verificacao is not None
    assert [(t.trecho_citado, t.localizacao) for t in v.trechos] == [("A IA mudou o ensino.", "§2")]


def test_verificar_sem_trecho_e_possivel(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    v = fontes.verificar(f.id, "verificada")
    assert v.status == "verificada" and v.trechos == []


def test_ligar_mais_trechos_a_fonte_verificada(fontes, interacoes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    fontes.verificar(f.id, "verificada", trecho="primeiro")
    fontes.ligar_trecho(f.id, "segundo", "linha 10")
    trechos = interacoes.obter(interacao.id).fontes[0].trechos
    assert sorted((t.trecho_citado, t.localizacao) for t in trechos) == [
        ("primeiro", None), ("segundo", "linha 10")
    ]


def test_nao_liga_trecho_a_fonte_incorreta_ou_nao_verificada(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Inventada (2099)")
    with pytest.raises(RegraViolada, match="verificada"):
        fontes.ligar_trecho(f.id, "x")
    with pytest.raises(RegraViolada, match="verificada"):
        fontes.verificar(f.id, "incorreta", trecho="x")
    assert fontes.obter(f.id).status == "nao_verificada"  # nada foi gravado


def test_trecho_vazio_e_resultado_invalido(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    with pytest.raises(RegraViolada, match="resultado"):
        fontes.verificar(f.id, "talvez")
    fontes.verificar(f.id, "verificada")
    with pytest.raises(RegraViolada, match="trecho"):
        fontes.ligar_trecho(f.id, "   ")


# ---------------------------------------------------------------- RF18
def test_anotacao_fica_salva_na_fonte(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Inventada (2099)")
    v = fontes.verificar(f.id, "incorreta", anotacao="  O DOI não existe.  ")
    assert v.status == "incorreta" and v.anotacao_correcao == "O DOI não existe."


def test_anotacao_vazia_nao_apaga_a_anterior(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    fontes.verificar(f.id, "incorreta", anotacao="Ano errado")
    v = fontes.verificar(f.id, "verificada", anotacao="")
    assert v.anotacao_correcao == "Ano errado"


def test_aluno_nao_mexe_em_fonte_de_outro(fontes, usuarios, entrar_como, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="Fonte não encontrada"):
        fontes.verificar(f.id, "verificada")
    with pytest.raises(RegraViolada, match="não encontrada"):
        fontes.adicionar(interacao.id, "x")
