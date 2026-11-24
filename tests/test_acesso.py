"""RF03: cada perfil só alcança o que é seu. No app não existe endereço digitado, então o
'acesso direto' é chamar o service sem passar pela tela: a regra tem que valer mesmo assim."""
import pytest

from services.erros import RegraViolada


@pytest.fixture
def tudo_da_ana(pesquisas, interacoes, fontes, entrar_como):
    entrar_como("ana@x.com")
    p = pesquisas.criar("Da Ana", "O")
    i = interacoes.registrar(p.id, "ChatGPT", "q", "r")
    f = fontes.adicionar(i.id, "Silva (2023)")
    return p, i, f


def _sair_e_entrar(usuarios, entrar_como, email, tipo="aluno", nome="Outro"):
    usuarios.sair()
    entrar_como(email, tipo=tipo, nome=nome)


def test_aluno_nao_acessa_nada_da_area_do_professor(relatorios, revisoes, usuarios, entrar_como, tudo_da_ana):
    p, i, f = tudo_da_ana
    chamadas = (
        lambda: revisoes.listar_todas(),
        lambda: revisoes.obter_pesquisa(p.id),
        lambda: revisoes.obter_interacao(i.id),
        lambda: revisoes.julgar_fonte(f.id, "verificada"),
        lambda: revisoes.comentar_interacao(i.id, "oi"),
        lambda: revisoes.confirmar_interacao(i.id),
        lambda: revisoes.reabrir_interacao(i.id),
        lambda: revisoes.aceitar(p.id),
        lambda: revisoes.devolver(p.id, "x"),
    )
    for chamada in chamadas:  # a própria dona
        with pytest.raises(RegraViolada, match="professores"):
            chamada()
    _sair_e_entrar(usuarios, entrar_como, "bia@x.com", nome="Bia")
    for chamada in chamadas:  # outro aluno
        with pytest.raises(RegraViolada, match="professores"):
            chamada()
    # e o relatório de outro aluno também não, mesmo sabendo o número
    with pytest.raises(RegraViolada, match="não encontrada"):
        relatorios.gerar(p.id)


def test_aluno_nao_ve_pesquisa_interacao_nem_fonte_de_outro(pesquisas, interacoes, fontes, usuarios, entrar_como, tudo_da_ana):
    p, i, f = tudo_da_ana
    _sair_e_entrar(usuarios, entrar_como, "bia@x.com", nome="Bia")
    assert pesquisas.listar_minhas() == []
    for chamada in (
        lambda: pesquisas.obter(p.id),
        lambda: pesquisas.editar(p.id, "x", "y"),
        lambda: pesquisas.entregar(p.id),
        lambda: interacoes.listar(p.id),
        lambda: interacoes.obter(i.id),
        lambda: interacoes.editar(i.id, "x", "q", "r"),
        lambda: interacoes.excluir(i.id),
        lambda: fontes.listar(i.id),
        lambda: fontes.obter(f.id),
        lambda: fontes.verificar(f.id, "verificada"),
    ):
        with pytest.raises(RegraViolada, match="não encontrada"):
            chamada()


def test_professor_nao_usa_as_funcoes_do_aluno(pesquisas, interacoes, fontes, usuarios, entrar_como, tudo_da_ana):
    p, i, f = tudo_da_ana
    _sair_e_entrar(usuarios, entrar_como, "prof@x.com", tipo="professor", nome="Prof")
    for chamada in (
        lambda: pesquisas.criar("T", "O"),
        lambda: pesquisas.listar_minhas(),
        lambda: pesquisas.obter(p.id),
        lambda: pesquisas.entregar(p.id),
        lambda: interacoes.registrar(p.id, "X", "q", "r"),
        lambda: interacoes.listar(p.id),
        lambda: fontes.adicionar(i.id, "x"),
        lambda: fontes.verificar(f.id, "verificada"),
    ):
        with pytest.raises(RegraViolada, match="alunos"):
            chamada()


def test_sem_login_nada_funciona(pesquisas, interacoes, fontes, relatorios, revisoes, usuarios, tudo_da_ana):
    p, i, f = tudo_da_ana
    usuarios.sair()
    for chamada in (
        lambda: pesquisas.listar_minhas(),
        lambda: pesquisas.entregar(p.id),
        lambda: interacoes.listar(p.id),
        lambda: fontes.listar(i.id),
        lambda: relatorios.gerar(p.id),
        lambda: revisoes.listar_todas(),
        lambda: revisoes.aceitar(p.id),
    ):
        with pytest.raises(RegraViolada, match="Entre"):
            chamada()
