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


# ---------------------------------------------------------------- RF08
def _concluir(pesquisa_id):
    """Ainda não existe o service de conclusão (RF10): marca direto no banco."""
    from tests.apoio import definir_status_das_pesquisas

    definir_status_das_pesquisas("concluida", pesquisa_id)


def test_editar_pesquisa_salva_a_alteracao(pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    editada = pesquisas.editar(p.id, "  Novo tema  ", " Novo objetivo ")
    assert editada.titulo == "Novo tema" and editada.objetivo == "Novo objetivo"
    # a alteração ficou gravada no banco, não só no objeto devolvido
    salva = pesquisas.obter(p.id)
    assert salva.titulo == "Novo tema" and salva.objetivo == "Novo objetivo"
    assert salva.status == "em_andamento"


def test_editar_pesquisa_exige_titulo_e_objetivo(pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    with pytest.raises(RegraViolada, match="título"):
        pesquisas.editar(p.id, "   ", "O")
    with pytest.raises(RegraViolada, match="objetivo"):
        pesquisas.editar(p.id, "T", "")
    salva = pesquisas.obter(p.id)
    assert salva.titulo == "Tema" and salva.objetivo == "Obj"


def test_pesquisa_concluida_nao_pode_ser_editada(pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    _concluir(p.id)
    with pytest.raises(RegraViolada, match="concluída"):
        pesquisas.editar(p.id, "Outro", "Outro")
    salva = pesquisas.obter(p.id)
    assert salva.titulo == "Tema" and salva.objetivo == "Obj"


def test_editar_pesquisa_de_outro_aluno_e_como_inexistente(pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    p = pesquisas.criar("Da Ana", "O")
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        pesquisas.editar(p.id, "Invadida", "O")
    usuarios.sair()
    entrar_como("a@x.com")
    assert pesquisas.obter(p.id).titulo == "Da Ana"


def test_editar_pesquisa_exige_aluno_logado(pesquisas, entrar_como):
    with pytest.raises(RegraViolada, match="Entre"):
        pesquisas.editar(1, "T", "O")
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    with pytest.raises(RegraViolada, match="alunos"):
        pesquisas.editar(1, "T", "O")


# ---------------------------------------------------------------- RF09
def test_excluir_pesquisa_em_andamento_leva_tudo_junto(pesquisas, interacoes, fontes, entrar_como):
    from tests.apoio import contar

    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    outra = pesquisas.criar("Fica", "Obj")
    i = interacoes.registrar(p.id, "ChatGPT", "P", "R")
    f = fontes.adicionar(i.id, "Silva (2023)")
    fontes.verificar(f.id, "verificada", trecho="Meu trecho")
    pesquisas.excluir(p.id)
    assert [x.titulo for x in pesquisas.listar_minhas()] == ["Fica"]
    with pytest.raises(RegraViolada, match="não encontrada"):
        pesquisas.obter(p.id)
    for colecao in ("interacoes", "fontes", "trechos"):
        assert contar(colecao) == 0
    assert contar("relatorios") == 1  # só o da pesquisa que ficou
    assert pesquisas.obter(outra.id).titulo == "Fica"


def test_pesquisa_entregue_nao_pode_ser_excluida(pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    pesquisas.entregar(p.id)
    with pytest.raises(RegraViolada, match="não pode ser excluída"):
        pesquisas.excluir(p.id)
    assert pesquisas.obter(p.id).status == "entregue"


def test_excluir_pesquisa_exige_ser_o_aluno_dono(pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    p = pesquisas.criar("Da Ana", "O")
    usuarios.sair()
    with pytest.raises(RegraViolada, match="Entre"):
        pesquisas.excluir(p.id)
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        pesquisas.excluir(p.id)
    usuarios.sair()
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    with pytest.raises(RegraViolada, match="alunos"):
        pesquisas.excluir(p.id)
    usuarios.sair()
    entrar_como("a@x.com")
    assert pesquisas.obter(p.id).titulo == "Da Ana"


# ---------------------------------------------------------------- RF10: entregar ao professor
def test_aluno_entrega_a_pesquisa_ao_professor(pesquisas, relatorios, entrar_como):
    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    entregue = pesquisas.entregar(p.id)
    assert entregue.status == "entregue" and entregue.data_entrega is not None
    assert entregue.data_conclusao is None  # concluir é do professor
    assert pesquisas.obter(p.id).status == "entregue"
    assert relatorios.gerar(p.id).entregue is True


def test_aluno_nao_tem_como_concluir_a_pesquisa(pesquisas):
    assert not hasattr(pesquisas, "concluir")


def test_pesquisa_entregue_nao_pode_ser_entregue_de_novo_nem_editada(pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("Tema", "Obj")
    pesquisas.entregar(p.id)
    with pytest.raises(RegraViolada, match="já foi entregue"):
        pesquisas.entregar(p.id)
    with pytest.raises(RegraViolada, match="entregue ao professor"):
        pesquisas.editar(p.id, "Outro", "Outro")


def test_entregar_exige_ser_o_aluno_dono(pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    p = pesquisas.criar("Da Ana", "O")
    usuarios.sair()
    with pytest.raises(RegraViolada, match="Entre"):
        pesquisas.entregar(p.id)
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        pesquisas.entregar(p.id)
    usuarios.sair()
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    with pytest.raises(RegraViolada, match="alunos"):
        pesquisas.entregar(p.id)
    assert pesquisas.repo.buscar_por_id(p.id).status == "em_andamento"
