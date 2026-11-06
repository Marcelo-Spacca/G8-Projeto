import pytest
from sqlalchemy import func, select, text

from repository.database import Session
from repository.models import Fonte, Interacao, Trecho
from services.erros import RegraViolada


def contar(modelo):
    with Session() as s:
        return s.scalar(select(func.count()).select_from(modelo))


@pytest.fixture
def interacao_com_fontes(interacoes, pesquisas, fontes, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    i = interacoes.registrar(p.id, "ChatGPT", "pergunta", "resposta")
    f1 = fontes.adicionar(i.id, "Silva (2023)")
    fontes.adicionar(i.id, "Souza (2020)")
    fontes.verificar(f1.id, "verificada", trecho="Meu parágrafo")
    return i


# ---------------------------------------------------------------- RF13
def test_editar_interacao_mantem_fontes_e_trechos(interacoes, interacao_com_fontes):
    i = interacao_com_fontes
    fontes_antes = sorted(f.id for f in interacoes.obter(i.id).fontes)

    editada = interacoes.editar(i.id, " Claude ", " pergunta corrigida ", " resposta corrigida ")

    assert (editada.ferramenta_ia, editada.pergunta, editada.resposta) == (
        "Claude", "pergunta corrigida", "resposta corrigida"
    )
    assert sorted(f.id for f in editada.fontes) == fontes_antes
    verificada = next(f for f in editada.fontes if f.referencia == "Silva (2023)")
    assert verificada.status == "verificada"
    assert [t.trecho_citado for t in verificada.trechos] == ["Meu parágrafo"]


def test_editar_exige_os_mesmos_campos_do_registro(interacoes, interacao_com_fontes):
    i = interacao_com_fontes
    with pytest.raises(RegraViolada, match="ferramenta"):
        interacoes.editar(i.id, " ", "q", "r")
    with pytest.raises(RegraViolada, match="pergunta"):
        interacoes.editar(i.id, "X", "", "r")
    with pytest.raises(RegraViolada, match="resposta"):
        interacoes.editar(i.id, "X", "q", None)
    assert interacoes.obter(i.id).pergunta == "pergunta"  # nada mudou


def test_aluno_nao_edita_nem_exclui_interacao_de_outro(interacoes, usuarios, entrar_como, interacao_com_fontes):
    usuarios.sair()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="Interação não encontrada"):
        interacoes.editar(interacao_com_fontes.id, "X", "q", "r")
    with pytest.raises(RegraViolada, match="Interação não encontrada"):
        interacoes.excluir(interacao_com_fontes.id)
    with pytest.raises(RegraViolada, match="Interação não encontrada"):
        interacoes.obter(99999)


def test_editar_e_excluir_exigem_login(interacoes, usuarios, interacao_com_fontes):
    usuarios.sair()
    with pytest.raises(RegraViolada, match="Entre"):
        interacoes.editar(interacao_com_fontes.id, "X", "q", "r")
    with pytest.raises(RegraViolada, match="Entre"):
        interacoes.excluir(interacao_com_fontes.id)


# ---------------------------------------------------------------- RF14
def test_excluir_interacao_apaga_fontes_e_trechos_junto(interacoes, interacao_com_fontes):
    assert (contar(Interacao), contar(Fonte), contar(Trecho)) == (1, 2, 1)
    interacoes.excluir(interacao_com_fontes.id)
    assert (contar(Interacao), contar(Fonte), contar(Trecho)) == (0, 0, 0)


def test_excluir_nao_afeta_outras_interacoes(interacoes, fontes, interacao_com_fontes):
    outra = interacoes.registrar(interacao_com_fontes.pesquisa_id, "Gemini", "q2", "r2")
    fontes.adicionar(outra.id, "Outra fonte")
    interacoes.excluir(interacao_com_fontes.id)
    assert [i.id for i in interacoes.listar(outra.pesquisa_id)] == [outra.id]
    assert contar(Fonte) == 1


def test_pesquisa_concluida_nao_permite_editar_nem_excluir(interacoes, interacao_com_fontes):
    with Session() as s:  # simula a conclusão (o RF10 ainda não existe)
        s.execute(text("UPDATE pesquisa SET status = 'concluida'"))
        s.commit()
    with pytest.raises(RegraViolada, match="concluída"):
        interacoes.editar(interacao_com_fontes.id, "X", "q", "r")
    with pytest.raises(RegraViolada, match="concluída"):
        interacoes.excluir(interacao_com_fontes.id)
    assert contar(Interacao) == 1
