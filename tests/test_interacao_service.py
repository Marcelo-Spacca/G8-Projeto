import pytest
from sqlalchemy import text

from repository.database import Session
from services.erros import RegraViolada


# ---------------------------------------------------------------- RF11
def test_registrar_interacao(interacoes, pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    i = interacoes.registrar(p.id, " ChatGPT ", " pergunta ", " resposta ")
    assert i.id and i.pesquisa_id == p.id and i.data_registro is not None
    assert (i.ferramenta_ia, i.pergunta, i.resposta) == ("ChatGPT", "pergunta", "resposta")


def test_registrar_exige_ferramenta_pergunta_e_resposta(interacoes, pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    with pytest.raises(RegraViolada, match="ferramenta"):
        interacoes.registrar(p.id, "", "q", "r")
    with pytest.raises(RegraViolada, match="pergunta"):
        interacoes.registrar(p.id, "X", " ", "r")
    with pytest.raises(RegraViolada, match="resposta"):
        interacoes.registrar(p.id, "X", "q", "")
    assert interacoes.listar(p.id) == []  # nada foi gravado


def test_registrar_exige_login(interacoes):
    with pytest.raises(RegraViolada, match="Entre"):
        interacoes.registrar(1, "X", "q", "r")


def test_nao_registra_em_pesquisa_de_outro_aluno_nem_inexistente(interacoes, pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    p = pesquisas.criar("T", "O")
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        interacoes.registrar(p.id, "X", "q", "r")
    with pytest.raises(RegraViolada, match="não encontrada"):
        interacoes.registrar(99999, "X", "q", "r")


def test_pesquisa_concluida_nao_aceita_interacao(interacoes, pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    with Session() as s:  # simula a conclusão (o RF10 ainda não existe)
        s.execute(text("UPDATE pesquisa SET status = 'concluida' WHERE id = :i"), {"i": p.id})
        s.commit()
    with pytest.raises(RegraViolada, match="concluída"):
        interacoes.registrar(p.id, "X", "q", "r")


# ---------------------------------------------------------------- RF12
def test_listar_interacoes_em_ordem_de_registro(interacoes, pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    interacoes.registrar(p.id, "ChatGPT", "pergunta 1", "resposta 1")
    interacoes.registrar(p.id, "Claude", "pergunta 2", "resposta 2")
    lista = interacoes.listar(p.id)
    assert [i.pergunta for i in lista] == ["pergunta 1", "pergunta 2"]
    assert [i.ferramenta_ia for i in lista] == ["ChatGPT", "Claude"]


def test_listar_so_mostra_interacoes_da_pesquisa_do_aluno(interacoes, pesquisas, usuarios, entrar_como):
    entrar_como("a@x.com")
    p = pesquisas.criar("T", "O")
    interacoes.registrar(p.id, "X", "q", "r")
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        interacoes.listar(p.id)
