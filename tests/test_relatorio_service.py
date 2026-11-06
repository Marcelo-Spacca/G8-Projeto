import pytest
from sqlalchemy import func, select

from repository.database import Session
from repository.models import Relatorio
from services.erros import RegraViolada


def contar_relatorios():
    with Session() as s:
        return s.scalar(select(func.count()).select_from(Relatorio))


@pytest.fixture
def pesquisa_completa(interacoes, pesquisas, fontes, usuarios, entrar_como):
    """Ana cria uma pesquisa com 1 interação e 3 fontes (uma de cada status) e sai."""
    entrar_como()
    p = pesquisas.criar("Impacto da IA", "Entender o uso de IA")
    i = interacoes.registrar(p.id, "ChatGPT", "Qual o efeito?", "Grande.")
    f1 = fontes.adicionar(i.id, "Silva (2023)")
    f2 = fontes.adicionar(i.id, "Inventada (2099)")
    fontes.adicionar(i.id, "Souza (2020)")
    fontes.verificar(f1.id, "verificada", anotacao="Confere", trecho="Meu texto", localizacao="§3")
    fontes.verificar(f2.id, "incorreta", anotacao="Não existe")
    usuarios.sair()
    return p


# ---------------------------------------------------------------- RF22
def test_relatorio_nasce_junto_com_a_pesquisa(pesquisas, entrar_como):
    entrar_como()
    p1 = pesquisas.criar("A", "O")
    p2 = pesquisas.criar("B", "O")
    assert contar_relatorios() == 2
    with Session() as s:
        ligados = set(s.scalars(select(Relatorio.pesquisa_id)))
    assert ligados == {p1.id, p2.id}


def test_gerar_varias_vezes_usa_sempre_o_mesmo_relatorio(relatorios, entrar_como, pesquisa_completa):
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    r1 = relatorios.gerar(pesquisa_completa.id)
    r2 = relatorios.gerar(pesquisa_completa.id)
    assert r1.relatorio.id == r2.relatorio.id
    assert r1.relatorio.pesquisa_id == pesquisa_completa.id
    assert contar_relatorios() == 1


# ---------------------------------------------------------------- RF20
def test_relatorio_reune_tudo_sem_digitacao(relatorios, entrar_como, pesquisa_completa):
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    r = relatorios.gerar(pesquisa_completa.id)

    assert r.pesquisa.titulo == "Impacto da IA" and r.pesquisa.aluno.nome == "Ana"
    assert r.relatorio.data_geracao is not None
    [i] = r.interacoes
    assert (i.pergunta, i.resposta) == ("Qual o efeito?", "Grande.")
    por_ref = {f.referencia: f for f in r.fontes}
    assert por_ref["Silva (2023)"].status == "verificada"
    assert por_ref["Silva (2023)"].trechos[0].trecho_citado == "Meu texto"
    assert por_ref["Inventada (2099)"].anotacao_correcao == "Não existe"
    assert r.contagem_status() == {"verificada": 1, "incorreta": 1, "nao_verificada": 1}


def test_relatorio_acompanha_edicoes_e_exclusoes(relatorios, interacoes, pesquisas, entrar_como):
    entrar_como()
    p = pesquisas.criar("T", "O")
    i = interacoes.registrar(p.id, "X", "q", "r")
    interacoes.editar(i.id, "X", "q corrigida", "r")
    assert relatorios.gerar(p.id).interacoes[0].pergunta == "q corrigida"
    interacoes.excluir(i.id)
    assert relatorios.gerar(p.id).interacoes == []


def test_aluno_ve_so_o_relatorio_das_proprias_pesquisas(relatorios, entrar_como, pesquisa_completa):
    entrar_como()  # Ana, a dona
    assert relatorios.gerar(pesquisa_completa.id).pesquisa.id == pesquisa_completa.id
    from services.sessao import sessao

    sessao.encerrar()
    entrar_como("b@x.com", nome="Bia")
    with pytest.raises(RegraViolada, match="não encontrada"):
        relatorios.gerar(pesquisa_completa.id)


def test_relatorio_exige_login_e_pesquisa_existente(relatorios, entrar_como):
    with pytest.raises(RegraViolada, match="Entre"):
        relatorios.gerar(1)
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    with pytest.raises(RegraViolada, match="não encontrada"):
        relatorios.gerar(99999)


def test_so_professor_lista_todas_as_pesquisas(relatorios, entrar_como, pesquisa_completa):
    entrar_como()
    with pytest.raises(RegraViolada, match="professores"):
        relatorios.listar_pesquisas()
    from services.sessao import sessao

    sessao.encerrar()
    entrar_como("p@x.com", tipo="professor", nome="Prof")
    [p] = relatorios.listar_pesquisas()
    assert p.titulo == "Impacto da IA" and p.aluno.nome == "Ana"
