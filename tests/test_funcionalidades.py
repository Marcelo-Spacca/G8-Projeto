import pytest

from repository.models import Fonte, Interacao, Relatorio, Trecho
from services.servicos import RegraViolada
from tests.conftest import contar
from ui.menu_console import formatar_relatorio


# ---------------------------------------------------------------- RF13 editar interação


def test_editar_interacao_mantem_fontes(svc, aluno, interacao):
    fontes_antes = sorted(f.id for f in interacao.fontes)

    svc.interacoes.editar(aluno.id, interacao.id, pergunta="O que é fotossíntese?")

    i = svc.interacoes.obter(aluno.id, interacao.id)
    assert i.pergunta == "O que é fotossíntese?"
    assert i.resposta == "É um processo..."  # campo vazio mantém o valor
    assert i.ferramenta_ia == "ChatGPT"
    assert sorted(f.id for f in i.fontes) == fontes_antes


def test_editar_interacao_mantem_trechos_e_verificacao(svc, aluno, interacao):
    fonte = interacao.fontes[0]
    svc.fontes.verificar(aluno.id, fonte.id, "verificada", trecho="Meu parágrafo")

    svc.interacoes.editar(aluno.id, interacao.id, resposta="Resposta corrigida")

    f = next(f for f in svc.interacoes.obter(aluno.id, interacao.id).fontes if f.id == fonte.id)
    assert f.status == "verificada"
    assert [t.trecho_citado for t in f.trechos] == ["Meu parágrafo"]


def test_outro_aluno_nao_edita(svc, interacao):
    intruso = svc.usuarios.cadastrar("Beto", "beto@ex.com", "segredo1", "aluno")
    with pytest.raises(RegraViolada):
        svc.interacoes.editar(intruso.id, interacao.id, pergunta="x")


# ---------------------------------------------------------------- RF14 excluir interação


def test_excluir_interacao_remove_fontes_e_trechos(sf, svc, aluno, interacao):
    svc.fontes.verificar(aluno.id, interacao.fontes[0].id, "verificada", trecho="T1")
    assert contar(sf, Fonte) == 2 and contar(sf, Trecho) == 1

    svc.interacoes.excluir(aluno.id, interacao.id)

    assert contar(sf, Interacao) == 0
    assert contar(sf, Fonte) == 0
    assert contar(sf, Trecho) == 0


def test_excluir_nao_afeta_outras_interacoes(sf, svc, aluno, pesquisa, interacao):
    outra = svc.interacoes.registrar(aluno.id, pesquisa.id, "Gemini", "P", "R", ["Fonte C"])
    svc.interacoes.excluir(aluno.id, interacao.id)
    assert [i.id for i in svc.interacoes.listar(aluno.id, pesquisa.id)] == [outra.id]
    assert contar(sf, Fonte) == 1


def test_menu_pede_confirmacao_antes_de_excluir(monkeypatch, sf, svc, aluno, interacao):
    from ui import menu_console

    menu = menu_console.MenuConsole.__new__(menu_console.MenuConsole)
    menu.interacoes, menu.fontes, menu.usuario = svc.interacoes, svc.fontes, aluno
    respostas = iter(["2", "n", "0"])  # excluir -> não confirma -> voltar
    monkeypatch.setattr("builtins.input", lambda *_: next(respostas))

    menu.menu_interacao(interacao.id)

    assert contar(sf, Interacao) == 1


# ---------------------------------------------------------------- RF26 / RF27 trechos


def test_verificar_com_trecho_salva_trecho_na_fonte(svc, aluno, interacao):
    fonte_id = interacao.fontes[0].id
    f = svc.fontes.verificar(
        aluno.id, fonte_id, "verificada", trecho="A luz é absorvida...", localizacao="§2"
    )
    assert f.status == "verificada"
    assert f.data_verificacao is not None
    assert [(t.trecho_citado, t.localizacao) for t in f.trechos] == [("A luz é absorvida...", "§2")]


def test_trecho_aparece_ao_lado_da_fonte_na_interacao(svc, aluno, interacao, capsys):
    from ui.menu_console import mostrar_interacao

    fonte_id = interacao.fontes[0].id
    svc.fontes.verificar(aluno.id, fonte_id, "verificada", trecho="Primeiro", localizacao="§1")
    svc.fontes.vincular_trecho(aluno.id, fonte_id, "Segundo")

    mostrar_interacao(svc.interacoes.obter(aluno.id, interacao.id))
    saida = capsys.readouterr().out
    pos_fonte = saida.index("Livro A")
    assert pos_fonte < saida.index('Trecho (§1): "Primeiro"') < saida.index("Artigo B")
    assert 'Trecho: "Segundo"' in saida


def test_nao_liga_trecho_a_fonte_incorreta_ou_nao_verificada(svc, aluno, interacao):
    fid = interacao.fontes[0].id
    with pytest.raises(RegraViolada):
        svc.fontes.verificar(aluno.id, fid, "incorreta", trecho="x")
    with pytest.raises(RegraViolada):
        svc.fontes.vincular_trecho(aluno.id, fid, "x")


def test_status_invalido(svc, aluno, interacao):
    with pytest.raises(RegraViolada):
        svc.fontes.verificar(aluno.id, interacao.fontes[0].id, "talvez")


# ---------------------------------------------------------------- RF18 anotação


def test_anotacao_salva_na_fonte_e_no_relatorio(svc, aluno, pesquisa, interacao):
    fid = interacao.fontes[1].id
    svc.fontes.verificar(aluno.id, fid, "incorreta", anotacao="A IA inventou o DOI")

    f = next(f for f in svc.interacoes.obter(aluno.id, interacao.id).fontes if f.id == fid)
    assert f.anotacao_correcao == "A IA inventou o DOI"

    texto = formatar_relatorio(svc.relatorios.gerar(aluno, pesquisa.id))
    assert "Anotação do aluno: A IA inventou o DOI" in texto


# ---------------------------------------------------------------- RF20 / RF22 relatório


def test_relatorio_criado_com_a_pesquisa(sf, svc, pesquisa):
    assert contar(sf, Relatorio) == 1


def test_relatorio_reune_tudo_sem_digitacao(svc, aluno, professor, pesquisa, interacao):
    f1, f2 = interacao.fontes
    svc.fontes.verificar(aluno.id, f1.id, "verificada", trecho="Meu texto", localizacao="§3")
    svc.fontes.verificar(aluno.id, f2.id, "incorreta", anotacao="Não existe")

    r = svc.relatorios.gerar(professor, pesquisa.id)

    assert r.pesquisa_id == pesquisa.id and r.aluno == "Ana"
    assert len(r.interacoes) == 1
    i = r.interacoes[0]
    assert (i.pergunta, i.resposta) == ("O que é?", "É um processo...")
    assert [(f.referencia, f.status) for f in i.fontes] == [
        ("Livro A", "verificada"),
        ("Artigo B", "incorreta"),
    ]
    assert i.fontes[0].trechos[0].texto == "Meu texto"
    assert r.contagem_status() == {"verificada": 1, "incorreta": 1, "nao_verificada": 0}
    texto = formatar_relatorio(r)
    assert "Fotossíntese" in texto and 'Trecho (§3): "Meu texto"' in texto


def test_relatorio_unico_por_pesquisa(sf, svc, aluno, professor, pesquisa):
    outra = svc.pesquisas.criar(aluno.id, "Outra", "Obj")
    r1 = svc.relatorios.gerar(professor, pesquisa.id)
    r1b = svc.relatorios.gerar(professor, pesquisa.id)
    r2 = svc.relatorios.gerar(professor, outra.id)

    assert r1.relatorio_id == r1b.relatorio_id != r2.relatorio_id
    assert r1.pesquisa_id == pesquisa.id and r2.pesquisa_id == outra.id
    assert contar(sf, Relatorio) == 2


def test_relatorio_reflete_edicoes_e_exclusoes(svc, aluno, pesquisa, interacao):
    svc.interacoes.editar(aluno.id, interacao.id, pergunta="Corrigida")
    assert svc.relatorios.gerar(aluno, pesquisa.id).interacoes[0].pergunta == "Corrigida"
    svc.interacoes.excluir(aluno.id, interacao.id)
    assert svc.relatorios.gerar(aluno, pesquisa.id).interacoes == []


def test_aluno_nao_ve_relatorio_de_outro(svc, pesquisa):
    intruso = svc.usuarios.cadastrar("Beto", "beto@ex.com", "segredo1", "aluno")
    with pytest.raises(RegraViolada):
        svc.relatorios.gerar(intruso, pesquisa.id)


# ---------------------------------------------------------------- base


def test_login(svc, aluno):
    assert svc.usuarios.entrar("ANA@ex.com", "segredo1").id == aluno.id
    with pytest.raises(RegraViolada):
        svc.usuarios.entrar("ana@ex.com", "errada")
