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


# ---------------------------------------------------------------- pesquisa entregue é o que o professor revisa: não muda
def test_pesquisa_entregue_trava_fontes(fontes, pesquisas, interacoes, interacao):
    f = fontes.adicionar(interacao.id, "Silva (2023)")
    fontes.verificar(f.id, "verificada", trecho="meu texto")
    pesquisas.entregar(interacao.pesquisa_id)
    with pytest.raises(RegraViolada, match="entregue ao professor"):
        fontes.adicionar(interacao.id, "Nova")
    with pytest.raises(RegraViolada, match="entregue ao professor"):
        fontes.verificar(f.id, "incorreta")
    with pytest.raises(RegraViolada, match="entregue ao professor"):
        fontes.ligar_trecho(f.id, "outro")
    ainda = fontes.obter(f.id)
    assert ainda.status == "verificada" and [t.trecho_citado for t in ainda.trechos] == ["meu texto"]


# ---------------------------------------------------------------- editar referência e link
def test_editar_corrige_referencia_e_link(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023", "http://velho.com")
    e = fontes.editar(f.id, "  SILVA, J. A educação na era da IA. 2023.  ", "  https://novo.com/artigo ")
    assert e.referencia == "SILVA, J. A educação na era da IA. 2023."
    assert e.link == "https://novo.com/artigo" and e.status == "nao_verificada"


def test_editar_pode_apagar_o_link(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023", "http://velho.com")
    assert fontes.editar(f.id, "Silva 2023", "   ").link is None


def test_editar_exige_referencia(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023")
    with pytest.raises(RegraViolada, match="referência"):
        fontes.editar(f.id, "  ", "http://x.com")
    assert fontes.obter(f.id).referencia == "Silva 2023"


def test_editar_fonte_verificada_zera_a_verificacao_e_os_trechos(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023")
    fontes.verificar(f.id, "verificada", "achei no site", "meu trecho", "§1")
    e = fontes.editar(f.id, "Silva 2024", None)
    assert e.status == "nao_verificada" and e.data_verificacao is None and e.anotacao_correcao is None
    assert e.trechos == [] and e.julgada_pelo_professor is False


def test_editar_fonte_incorreta_tambem_volta_a_nao_verificada(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Livro inventado")
    fontes.verificar(f.id, "incorreta", "não existe")
    assert fontes.editar(f.id, "Livro real", None).status == "nao_verificada"


def test_editar_sem_mudar_nada_preserva_a_verificacao(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023", "http://x.com")
    fontes.verificar(f.id, "verificada", "ok", "trecho")
    e = fontes.editar(f.id, " Silva 2023 ", "http://x.com ")
    assert e.status == "verificada" and len(e.trechos) == 1 and e.anotacao_correcao == "ok"


def test_so_o_link_mudando_tambem_exige_nova_verificacao(fontes, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023", "http://x.com")
    fontes.verificar(f.id, "verificada")
    assert fontes.editar(f.id, "Silva 2023", "http://y.com").status == "nao_verificada"


def test_nao_edita_fonte_de_pesquisa_entregue_nem_de_interacao_confirmada(fontes, interacoes, pesquisas, revisoes, entrar_como, interacao):
    f = fontes.adicionar(interacao.id, "Silva 2023")
    pesquisas.entregar(interacao.pesquisa_id)
    with pytest.raises(RegraViolada, match="entregue ao professor"):
        fontes.editar(f.id, "Outra", None)
    entrar_como("prof@x.com", tipo="professor", nome="Prof")
    revisoes.julgar_fonte(f.id, "verificada")
    revisoes.confirmar_interacao(interacao.id)
    revisoes.devolver(interacao.pesquisa_id, "ajuste")
    entrar_como("ana@x.com")
    with pytest.raises(RegraViolada, match="confirmada pelo professor"):
        fontes.editar(f.id, "Outra", None)


def test_aluno_nao_edita_fonte_de_outro_aluno(fontes, interacao, usuarios, entrar_como):
    f = fontes.adicionar(interacao.id, "Silva 2023")
    usuarios.sair()
    entrar_como("bia@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="Fonte não encontrada"):
        fontes.editar(f.id, "Hackeada", None)
