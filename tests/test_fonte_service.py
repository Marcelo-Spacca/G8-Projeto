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



# ---------------------------------------------------------------- RF15
def test_fonte_guarda_referencia_e_link(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)", "  https://doi.org/10.1/x  ")
    assert (f.referencia, f.link) == ("Silva (2023)", "https://doi.org/10.1/x")
    assert fontes.obter(f.id).link == "https://doi.org/10.1/x"


def test_link_e_opcional(fontes, interacao):
    assert fontes.adicionar(interacao.id, "Sem link").link is None
    assert fontes.adicionar(interacao.id, "Link vazio", "   ").link is None


def test_uma_interacao_aceita_varias_fontes(fontes, interacao):
    for ref in ("A", "B", "C"):
        fontes.adicionar(interacao.id, ref)
    assert [f.referencia for f in fontes.listar(interacao.id)] == ["A", "B", "C"]


# ---------------------------------------------------------------- RF16
def test_toda_fonte_nova_comeca_nao_verificada(fontes, interacao):
    todas = [fontes.adicionar(interacao.id, r, link) for r, link in (("A", None), ("B", "https://x.org"))]
    assert [f.status for f in todas] == ["nao_verificada", "nao_verificada"]
    assert all(f.data_verificacao is None for f in todas)


# ---------------------------------------------------------------- RF17
def test_status_vai_de_um_para_outro_nos_tres_sentidos(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    assert fontes.verificar(f.id, "verificada").status == "verificada"
    assert fontes.verificar(f.id, "incorreta").status == "incorreta"
    voltou = fontes.verificar(f.id, "nao_verificada")
    assert voltou.status == "nao_verificada" and voltou.data_verificacao is None
    assert fontes.verificar(f.id, "verificada").data_verificacao is not None


def test_deixar_de_ser_verificada_remove_os_trechos_ligados(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    fontes.verificar(f.id, "verificada", trecho="primeiro")
    fontes.ligar_trecho(f.id, "segundo")
    assert len(fontes.obter(f.id).trechos) == 2
    assert fontes.verificar(f.id, "incorreta", anotacao="Era outro ano").trechos == []
    # voltando a verificada, ela começa sem trechos
    assert fontes.verificar(f.id, "verificada").trechos == []


def test_nao_verificada_tambem_nao_aceita_trecho(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    with pytest.raises(RegraViolada, match="verificada"):
        fontes.verificar(f.id, "nao_verificada", trecho="x")


# ---------------------------------------------------------------- RF19
def test_listar_fontes_mostra_cada_uma_com_o_status_atual(fontes, interacao):
    a = fontes.adicionar(interacao.id, "A")
    b = fontes.adicionar(interacao.id, "B")
    fontes.adicionar(interacao.id, "C")
    fontes.verificar(a.id, "verificada")
    fontes.verificar(b.id, "incorreta")
    lista = fontes.listar(interacao.id)
    assert [(f.referencia, f.status) for f in lista] == [
        ("A", "verificada"), ("B", "incorreta"), ("C", "nao_verificada")
    ]
    from services.fonte_service import contar_status

    assert contar_status(lista) == {"verificada": 1, "incorreta": 1, "nao_verificada": 1}


def test_so_o_dono_lista_as_fontes_da_interacao(fontes, usuarios, entrar_como, interacao):
    usuarios.sair()
    with pytest.raises(RegraViolada, match="Entre"):
        fontes.listar(interacao.id)
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        fontes.listar(interacao.id)


# ---------------------------------------------------------------- pesquisa concluída é o que foi entregue: não muda mais
def test_pesquisa_concluida_trava_fontes(fontes, pesquisas, interacoes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    fontes.verificar(f.id, "verificada", trecho="meu texto")
    pesquisas.concluir(interacao.pesquisa_id)
    with pytest.raises(RegraViolada, match="concluída"):
        fontes.adicionar(interacao.id, "Nova")
    with pytest.raises(RegraViolada, match="concluída"):
        fontes.verificar(f.id, "incorreta")
    with pytest.raises(RegraViolada, match="concluída"):
        fontes.ligar_trecho(f.id, "outro")
    ainda = fontes.obter(f.id)
    assert ainda.status == "verificada" and [t.trecho_citado for t in ainda.trechos] == ["meu texto"]
