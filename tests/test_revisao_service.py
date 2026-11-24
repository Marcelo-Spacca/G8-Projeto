"""Fluxo de revisão: o aluno entrega; o professor julga as fontes, comenta, confirma e então
aceita ou devolve (com mensagem). Interação confirmada não muda mais para o aluno."""
import pytest

from services.erros import RegraViolada
from services.sessao import sessao


@pytest.fixture
def cena(pesquisas, interacoes, fontes, usuarios, entrar_como):
    """Ana tem uma pesquisa com duas interações (a 1ª com duas fontes), ainda em andamento."""

    class Cena:
        pass

    c = Cena()
    entrar_como("ana@x.com")
    c.pesquisa = pesquisas.criar("Impacto da IA", "Entender o uso de IA")
    c.i1 = interacoes.registrar(c.pesquisa.id, "ChatGPT", "P1", "R1")
    c.i2 = interacoes.registrar(c.pesquisa.id, "Claude", "P2", "R2")
    c.f1 = fontes.adicionar(c.i1.id, "Silva (2023)")
    c.f2 = fontes.adicionar(c.i1.id, "Souza (2020)")
    c.f3 = fontes.adicionar(c.i2.id, "Lima (2021)")
    c.ana = lambda: (sessao.encerrar(), entrar_como("ana@x.com"))
    c.prof = lambda: (sessao.encerrar(), entrar_como("prof@x.com", tipo="professor", nome="Prof"))
    return c


@pytest.fixture
def entregue(cena, pesquisas):
    pesquisas.entregar(cena.pesquisa.id)
    cena.prof()
    return cena


# ---------------------------------------------------------------- acompanhar
def test_professor_acompanha_pesquisa_em_andamento_sem_alterar(cena, revisoes):
    cena.prof()
    [p] = revisoes.listar_todas()
    assert p.status == "em_andamento" and p.aluno.nome == "Ana" and len(p.interacoes) == 2
    detalhe = revisoes.obter_pesquisa(cena.pesquisa.id)
    assert [i.pergunta for i in detalhe.interacoes] == ["P1", "P2"]
    assert len(revisoes.obter_interacao(cena.i1.id).fontes) == 2
    for chamada in (
        lambda: revisoes.julgar_fonte(cena.f1.id, "verificada"),
        lambda: revisoes.comentar_interacao(cena.i1.id, "oi"),
        lambda: revisoes.confirmar_interacao(cena.i1.id),
        lambda: revisoes.aceitar(cena.pesquisa.id),
        lambda: revisoes.devolver(cena.pesquisa.id, "x"),
    ):
        with pytest.raises(RegraViolada, match="ainda não entregou"):
            chamada()


def test_professor_ve_pesquisas_de_varios_alunos(cena, revisoes, pesquisas, usuarios, entrar_como):
    sessao.encerrar()
    entrar_como("bia@x.com", nome="Bia")
    pesquisas.criar("Da Bia", "O")
    cena.prof()
    assert sorted(p.aluno.nome for p in revisoes.listar_todas()) == ["Ana", "Bia"]


# ---------------------------------------------------------------- entrega trava o aluno
def test_pesquisa_entregue_fica_travada_para_o_aluno(cena, pesquisas, interacoes, fontes):
    pesquisas.entregar(cena.pesquisa.id)
    for chamada in (
        lambda: pesquisas.editar(cena.pesquisa.id, "x", "y"),
        lambda: pesquisas.excluir(cena.pesquisa.id),
        lambda: interacoes.registrar(cena.pesquisa.id, "X", "q", "r"),
        lambda: interacoes.editar(cena.i1.id, "X", "q", "r"),
        lambda: interacoes.excluir(cena.i1.id),
        lambda: fontes.adicionar(cena.i1.id, "Nova"),
        lambda: fontes.verificar(cena.f1.id, "verificada"),
    ):
        with pytest.raises(RegraViolada, match="entregue ao professor"):
            chamada()


# ---------------------------------------------------------------- julgar fontes
def test_professor_julga_e_desverifica_fontes(entregue, revisoes, fontes):
    f = revisoes.julgar_fonte(entregue.f1.id, "verificada", "Confere com o catálogo")
    assert f.status == "verificada" and f.julgada_pelo_professor and f.anotacao_correcao == "Confere com o catálogo"
    f = revisoes.julgar_fonte(entregue.f1.id, "incorreta", "O ano está errado")
    assert f.status == "incorreta" and f.anotacao_correcao == "O ano está errado"
    f = revisoes.julgar_fonte(entregue.f1.id, "nao_verificada")  # "desverificar"
    assert f.status == "nao_verificada" and f.data_verificacao is None
    with pytest.raises(RegraViolada, match="Escolha"):
        revisoes.julgar_fonte(entregue.f1.id, "talvez")
    with pytest.raises(RegraViolada, match="Fonte não encontrada"):
        revisoes.julgar_fonte(99999, "verificada")


def test_julgar_fonte_remove_os_trechos_ligados_como_no_aluno(cena, pesquisas, fontes, revisoes):
    fontes.verificar(cena.f1.id, "verificada", trecho="meu texto")
    pesquisas.entregar(cena.pesquisa.id)
    cena.prof()
    f = revisoes.julgar_fonte(cena.f1.id, "incorreta")
    assert f.trechos == []


# ---------------------------------------------------------------- comentar
def test_professor_comenta_e_apaga_o_comentario(entregue, revisoes):
    i = revisoes.comentar_interacao(entregue.i1.id, "  Falta citar o ano.  ")
    assert i.comentario_professor == "Falta citar o ano." and i.data_comentario is not None
    i = revisoes.comentar_interacao(entregue.i1.id, "   ")
    assert i.comentario_professor is None and i.data_comentario is None


def test_aluno_le_o_comentario_mas_nao_o_escreve(entregue, revisoes, interacoes):
    revisoes.comentar_interacao(entregue.i2.id, "Boa pergunta.")
    entregue.ana()
    assert interacoes.obter(entregue.i2.id).comentario_professor == "Boa pergunta."
    assert not hasattr(interacoes, "comentar_interacao") and not hasattr(interacoes, "comentar")


# ---------------------------------------------------------------- confirmar
def test_confirmar_exige_todas_as_fontes_julgadas(entregue, revisoes):
    revisoes.julgar_fonte(entregue.f1.id, "verificada")
    with pytest.raises(RegraViolada, match="Julgue todas"):
        revisoes.confirmar_interacao(entregue.i1.id)
    revisoes.julgar_fonte(entregue.f2.id, "incorreta")
    assert revisoes.confirmar_interacao(entregue.i1.id).confirmada is True
    with pytest.raises(RegraViolada, match="já está confirmada"):
        revisoes.confirmar_interacao(entregue.i1.id)


def test_interacao_sem_fontes_pode_ser_confirmada(cena, revisoes, interacoes, pesquisas):
    vazia = interacoes.registrar(cena.pesquisa.id, "Gemini", "P3", "R3")
    pesquisas.entregar(cena.pesquisa.id)
    cena.prof()
    assert revisoes.confirmar_interacao(vazia.id).confirmada is True


def test_interacao_confirmada_nao_aceita_julgamento_ate_ser_reaberta(entregue, revisoes):
    revisoes.julgar_fonte(entregue.f3.id, "verificada")
    revisoes.confirmar_interacao(entregue.i2.id)
    with pytest.raises(RegraViolada, match="confirmada"):
        revisoes.julgar_fonte(entregue.f3.id, "incorreta")
    assert revisoes.reabrir_interacao(entregue.i2.id).confirmada is False
    assert revisoes.julgar_fonte(entregue.f3.id, "incorreta").status == "incorreta"
    with pytest.raises(RegraViolada, match="não está confirmada"):
        revisoes.reabrir_interacao(entregue.i2.id)


# ---------------------------------------------------------------- devolver
def test_devolver_exige_mensagem_e_volta_a_em_andamento(entregue, revisoes, pesquisas):
    with pytest.raises(RegraViolada, match="mensagem"):
        revisoes.devolver(entregue.pesquisa.id, "   ")
    assert revisoes.obter_pesquisa(entregue.pesquisa.id).status == "entregue"
    p = revisoes.devolver(entregue.pesquisa.id, "  Verifique a fonte Souza (2020).  ")
    assert p.status == "em_andamento" and p.devolvida is True
    assert p.mensagem_devolucao == "Verifique a fonte Souza (2020)." and p.data_devolucao is not None
    assert p.data_entrega is None
    entregue.ana()
    visto = pesquisas.obter(entregue.pesquisa.id)  # a mensagem fica visível para o aluno
    assert visto.mensagem_devolucao == "Verifique a fonte Souza (2020)."


def test_aluno_reajusta_a_pesquisa_devolvida_e_entrega_de_novo(entregue, revisoes, pesquisas, interacoes, fontes):
    revisoes.julgar_fonte(entregue.f1.id, "incorreta", "Não existe")
    revisoes.comentar_interacao(entregue.i1.id, "Troque esta fonte.")
    revisoes.devolver(entregue.pesquisa.id, "Há fonte inventada.")
    entregue.ana()
    pesquisas.editar(entregue.pesquisa.id, "Novo título", "Novo objetivo")
    interacoes.editar(entregue.i1.id, "ChatGPT", "P1 ajustada", "R1")
    nova = fontes.adicionar(entregue.i1.id, "Correta (2024)")
    assert nova.status == "nao_verificada"
    refeita = fontes.verificar(entregue.f1.id, "nao_verificada")  # o aluno também reajusta o que o professor julgou
    assert refeita.julgada_pelo_professor is False
    assert interacoes.obter(entregue.i1.id).comentario_professor == "Troque esta fonte."
    again = pesquisas.entregar(entregue.pesquisa.id)
    assert again.status == "entregue" and again.data_entrega is not None


def test_interacao_confirmada_fica_fechada_depois_de_devolvida(entregue, revisoes, pesquisas, interacoes, fontes):
    revisoes.julgar_fonte(entregue.f3.id, "verificada")
    revisoes.confirmar_interacao(entregue.i2.id)
    revisoes.devolver(entregue.pesquisa.id, "Ajuste a primeira interação.")
    entregue.ana()
    for chamada in (
        lambda: interacoes.editar(entregue.i2.id, "X", "q", "r"),
        lambda: interacoes.excluir(entregue.i2.id),
        lambda: fontes.adicionar(entregue.i2.id, "Nova"),
        lambda: fontes.verificar(entregue.f3.id, "incorreta"),
        lambda: fontes.ligar_trecho(entregue.f3.id, "x"),
    ):
        with pytest.raises(RegraViolada, match="confirmada pelo professor"):
            chamada()
    # a interação não confirmada continua livre, e o aluno cria uma nova no lugar da fechada
    interacoes.editar(entregue.i1.id, "ChatGPT", "ajustada", "R1")
    assert interacoes.registrar(entregue.pesquisa.id, "Claude", "P3", "R3").confirmada is False


# ---------------------------------------------------------------- aceitar
def test_aceitar_conclui_confirma_tudo_e_trava(entregue, revisoes, pesquisas, interacoes, relatorios):
    p = revisoes.aceitar(entregue.pesquisa.id)
    assert p.status == "concluida" and p.data_conclusao is not None
    assert all(i.confirmada for i in revisoes.obter_pesquisa(p.id).interacoes)
    with pytest.raises(RegraViolada, match="já foi concluída"):
        revisoes.aceitar(p.id)
    with pytest.raises(RegraViolada, match="já foi concluída"):
        revisoes.devolver(p.id, "tarde demais")
    with pytest.raises(RegraViolada, match="já foi concluída"):
        revisoes.julgar_fonte(entregue.f1.id, "verificada")
    entregue.ana()
    with pytest.raises(RegraViolada, match="concluída pelo professor"):
        pesquisas.editar(p.id, "x", "y")
    with pytest.raises(RegraViolada, match="concluída pelo professor"):
        interacoes.registrar(p.id, "X", "q", "r")
    assert relatorios.gerar(p.id).concluida is True


def test_aceitar_limpa_a_mensagem_de_uma_devolucao_antiga(entregue, revisoes, pesquisas):
    revisoes.devolver(entregue.pesquisa.id, "Ajuste.")
    entregue.ana()
    pesquisas.entregar(entregue.pesquisa.id)
    entregue.prof()
    assert revisoes.aceitar(entregue.pesquisa.id).mensagem_devolucao is None


def test_nao_aceita_nem_devolve_pesquisa_inexistente(entregue, revisoes):
    with pytest.raises(RegraViolada, match="Pesquisa não encontrada"):
        revisoes.aceitar(99999)
    with pytest.raises(RegraViolada, match="Pesquisa não encontrada"):
        revisoes.devolver(99999, "x")
    with pytest.raises(RegraViolada, match="Interação não encontrada"):
        revisoes.obter_interacao(99999)
