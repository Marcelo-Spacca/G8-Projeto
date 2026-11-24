"""Grupos: criar, convidar, aceitar (nasce a pesquisa do grupo) e a gestão do professor."""
import pytest

from services.erros import RegraViolada
from services.sessao import sessao


@pytest.fixture
def como(entrar_como):
    def _como(email, tipo="aluno", nome=None):
        sessao.encerrar()
        return entrar_como(email, tipo=tipo, nome=nome or email.split("@")[0].title())

    return _como


@pytest.fixture
def cenario(como, turmas):
    """Turma COM grupos, professor 'prof', alunos Ana, Bia e Caio matriculados."""
    como("prof@x.com", "professor")
    turma = turmas.criar("Cálculo I", permite_grupos=True)
    ids = {}
    for email in ("ana@x.com", "bia@x.com", "caio@x.com"):
        ids[email.split("@")[0]] = como(email).id
        turmas.entrar(turma.codigo)
    como("ana@x.com")
    return turma, ids


@pytest.fixture
def grupo(cenario, grupos):
    turma, _ = cenario
    return grupos.criar(turma.id, "Time A", "Impacto da IA", "Medir o impacto")


@pytest.fixture
def grupo_com_bia(grupo, grupos, cenario, como):
    """Ana criou o grupo e convidou a Bia, que aceitou: a pesquisa do grupo já existe."""
    _, ids = cenario
    grupos.convidar(grupo.id, [ids["bia"]])
    como("bia@x.com")
    convite = grupos.convites_pendentes(grupo.turma_id)[0]
    como("bia@x.com")
    grupos.responder_convite(convite.id, True)
    como("ana@x.com")
    return grupos.obter(grupo.id)


# ---------------------------------------------------------------- criar
def test_turma_sem_grupos_recusa_criar_e_nao_tem_convites(como, turmas, grupos):
    como("prof@x.com", "professor")
    turma = turmas.criar("Sem grupos")
    como("ana@x.com")
    turmas.entrar(turma.codigo)
    with pytest.raises(RegraViolada, match="não permite grupos"):
        grupos.criar(turma.id, "G", "T", "O")
    assert grupos.convites_pendentes(turma.id) == []


def test_criar_grupo_deixa_o_criador_como_integrante_e_ainda_sem_pesquisa(grupo, cenario):
    _, ids = cenario
    assert grupo.nome == "Time A" and grupo.criador_id == ids["ana"]
    assert [a.nome for a in grupo.alunos] == ["Ana"]
    assert grupo.pesquisa is None


@pytest.mark.parametrize(
    "nome,titulo,objetivo,trecho",
    [("", "T", "O", "nome ao grupo"), ("G", " ", "O", "título"), ("G", "T", "", "objetivo")],
)
def test_criar_grupo_valida_os_campos(grupos, cenario, nome, titulo, objetivo, trecho):
    turma, _ = cenario
    with pytest.raises(RegraViolada, match=trecho):
        grupos.criar(turma.id, nome, titulo, objetivo)


def test_so_aluno_da_turma_cria_grupo(grupos, cenario, como):
    turma, _ = cenario
    como("dani@x.com")  # não entrou na turma
    with pytest.raises(RegraViolada, match="Turma não encontrada"):
        grupos.criar(turma.id, "G", "T", "O")
    como("prof@x.com", "professor")
    with pytest.raises(RegraViolada, match="exclusiva de alunos"):
        grupos.criar(turma.id, "G", "T", "O")


# ---------------------------------------------------------------- convidar e responder
def test_convidaveis_sao_os_colegas_fora_do_grupo_e_sem_convite_pendente(grupo, grupos, cenario):
    _, ids = cenario
    assert [a.nome for a in grupos.convidaveis(grupo.id)] == ["Bia", "Caio"]
    grupos.convidar(grupo.id, [ids["bia"]])
    assert [a.nome for a in grupos.convidaveis(grupo.id)] == ["Caio"]


def test_convidar_gera_convite_pendente_para_o_colega(grupo, grupos, cenario, como):
    turma, ids = cenario
    assert grupos.convidar(grupo.id, [ids["bia"], ids["caio"], ids["bia"]]) == 2  # repetido conta uma vez
    como("bia@x.com")
    convites = grupos.convites_pendentes(turma.id)
    assert len(convites) == 1 and convites[0].grupo.nome == "Time A" and convites[0].convidado_por.nome == "Ana"
    como("ana@x.com")
    assert grupos.convites_pendentes(turma.id) == []  # quem convidou não tem convite


def test_convidar_valida_a_lista(grupo, grupos, cenario, como, turmas):
    turma, ids = cenario
    with pytest.raises(RegraViolada, match="pelo menos um colega"):
        grupos.convidar(grupo.id, [])
    with pytest.raises(RegraViolada, match="Só é possível convidar"):
        grupos.convidar(grupo.id, [ids["ana"]])  # ela mesma
    como("dani@x.com")
    dani = sessao.usuario.id  # fora da turma
    como("ana@x.com")
    with pytest.raises(RegraViolada, match="Só é possível convidar"):
        grupos.convidar(grupo.id, [dani])
    grupos.convidar(grupo.id, [ids["bia"]])
    with pytest.raises(RegraViolada, match="Só é possível convidar"):
        grupos.convidar(grupo.id, [ids["bia"]])  # já tem convite pendente


def test_so_integrante_convida(grupo, grupos, cenario, como):
    _, ids = cenario
    como("caio@x.com")
    with pytest.raises(RegraViolada, match="Grupo não encontrado"):
        grupos.convidar(grupo.id, [ids["bia"]])
    with pytest.raises(RegraViolada, match="Grupo não encontrado"):
        grupos.obter(grupo.id)


def test_aceitar_o_convite_cria_a_pesquisa_do_grupo(grupo_com_bia, grupos, pesquisas, cenario, como):
    turma, ids = cenario
    g = grupo_com_bia
    assert sorted(a.nome for a in g.alunos) == ["Ana", "Bia"]
    p = g.pesquisa
    assert p is not None and p.titulo == "Impacto da IA" and p.objetivo == "Medir o impacto"
    assert p.grupo_id == g.id and p.aluno_id is None and p.turma_id == turma.id and p.de_grupo
    # as duas alunas enxergam a mesma pesquisa; não aparece nas individuais
    assert [x.id for x in pesquisas.listar_de_grupo(turma.id)] == [p.id]
    assert pesquisas.listar_minhas(turma.id) == []
    como("bia@x.com")
    assert [x.id for x in pesquisas.listar_de_grupo(turma.id)] == [p.id]
    assert pesquisas.obter(p.id).autor == "Time A"
    assert grupos.convites_pendentes(turma.id) == []


def test_recusar_nao_cria_pesquisa_e_permite_convidar_de_novo(grupo, grupos, cenario, como):
    turma, ids = cenario
    grupos.convidar(grupo.id, [ids["bia"]])
    como("bia@x.com")
    convite = grupos.convites_pendentes(turma.id)[0]
    g = grupos.responder_convite(convite.id, False)
    assert g.pesquisa is None and [a.nome for a in g.alunos] == ["Ana"]
    como("ana@x.com")
    assert "Bia" in [a.nome for a in grupos.convidaveis(grupo.id)]
    grupos.convidar(grupo.id, [ids["bia"]])
    como("bia@x.com")
    assert len(grupos.convites_pendentes(turma.id)) == 1


def test_convite_respondido_nao_responde_de_novo_e_so_o_convidado_responde(grupo, grupos, cenario, como):
    turma, ids = cenario
    grupos.convidar(grupo.id, [ids["bia"]])
    como("caio@x.com")
    convite_id = None
    como("bia@x.com")
    convite_id = grupos.convites_pendentes(turma.id)[0].id
    como("caio@x.com")
    with pytest.raises(RegraViolada, match="Convite não encontrado"):
        grupos.responder_convite(convite_id, True)
    como("bia@x.com")
    grupos.responder_convite(convite_id, True)
    with pytest.raises(RegraViolada, match="já foi respondido"):
        grupos.responder_convite(convite_id, True)
    with pytest.raises(RegraViolada, match="Convite não encontrado"):
        grupos.responder_convite(9999, True)


def test_segundo_aceite_nao_cria_outra_pesquisa(grupo_com_bia, grupos, pesquisas, cenario, como):
    turma, ids = cenario
    pesquisa_id = grupo_com_bia.pesquisa.id
    grupos.convidar(grupo_com_bia.id, [ids["caio"]])
    como("caio@x.com")
    grupos.responder_convite(grupos.convites_pendentes(turma.id)[0].id, True)
    g = grupos.obter(grupo_com_bia.id)
    assert sorted(a.nome for a in g.alunos) == ["Ana", "Bia", "Caio"]
    assert g.pesquisa.id == pesquisa_id
    assert [p.id for p in pesquisas.listar_de_grupo(turma.id)] == [pesquisa_id]


def test_aluno_pode_ter_varios_grupos_na_mesma_turma(grupos, cenario):
    turma, _ = cenario
    grupos.criar(turma.id, "G1", "T1", "O")
    grupos.criar(turma.id, "G2", "T2", "O")
    assert {g.nome for g in grupos.listar_do_aluno(turma.id)} == {"G1", "G2"}


# ---------------------------------------------------------------- trabalhar na pesquisa do grupo
def test_integrantes_registram_interacoes_na_mesma_pesquisa(grupo_com_bia, interacoes, fontes, como):
    pid = grupo_com_bia.pesquisa.id
    interacoes.registrar(pid, "ChatGPT", "pergunta da Ana", "r")
    como("bia@x.com")
    i2 = interacoes.registrar(pid, "Claude", "pergunta da Bia", "r")
    fontes.adicionar(i2.id, "Ref da Bia", "https://ex.com")
    como("ana@x.com")
    assert [i.pergunta for i in interacoes.listar(pid)] == ["pergunta da Ana", "pergunta da Bia"]
    # a Ana edita a fonte que a Bia cadastrou
    f = interacoes.obter(i2.id).fontes[0]
    assert fontes.editar(f.id, "Ref corrigida", None).referencia == "Ref corrigida"


def test_quem_nao_e_do_grupo_nao_alcanca_a_pesquisa(grupo_com_bia, pesquisas, interacoes, relatorios, como):
    pid = grupo_com_bia.pesquisa.id
    i = interacoes.registrar(pid, "IA", "q", "r")
    como("caio@x.com")  # na turma, mas não no grupo
    for acao in (lambda: pesquisas.obter(pid), lambda: interacoes.listar(pid), lambda: interacoes.obter(i.id),
                 lambda: relatorios.gerar(pid), lambda: pesquisas.entregar(pid)):
        with pytest.raises(RegraViolada, match="não encontrada"):
            acao()


def test_pesquisa_de_grupo_nao_e_excluida_pelos_alunos(grupo_com_bia, pesquisas):
    with pytest.raises(RegraViolada, match="de grupo não podem ser excluídas"):
        pesquisas.excluir(grupo_com_bia.pesquisa.id)


def test_integrante_entrega_e_o_professor_aceita_o_trabalho_do_grupo(grupo_com_bia, pesquisas, relatorios, revisoes, como, cenario):
    turma, _ = cenario
    pid = grupo_com_bia.pesquisa.id
    como("bia@x.com")
    pesquisas.entregar(pid)
    como("ana@x.com")
    assert pesquisas.obter(pid).status == "entregue"
    assert relatorios.gerar(pid).pesquisa.grupo.nome == "Time A"  # relatório do aluno
    como("prof@x.com", "professor")
    p = revisoes.listar_todas(turma.id)[0]
    assert p.autor == "Time A" and [a.nome for a in p.grupo.alunos] == ["Ana", "Bia"]
    revisoes.aceitar(pid)
    assert relatorios.gerar(pid).concluida


def test_integrantes_nao_mudam_depois_da_entrega(grupo_com_bia, grupos, pesquisas, cenario, como):
    _, ids = cenario
    pesquisas.entregar(grupo_com_bia.pesquisa.id)
    with pytest.raises(RegraViolada, match="foi entregue ao professor"):
        grupos.convidar(grupo_com_bia.id, [ids["caio"]])
    como("prof@x.com", "professor")
    with pytest.raises(RegraViolada, match="foi entregue ao professor"):
        grupos.atribuir_aluno(grupo_com_bia.id, ids["caio"])
    with pytest.raises(RegraViolada, match="foi entregue ao professor"):
        grupos.remover_aluno(grupo_com_bia.id, ids["bia"])


def test_convite_pendente_nao_e_aceito_com_a_pesquisa_entregue(grupo_com_bia, grupos, pesquisas, cenario, como):
    turma, ids = cenario
    grupos.convidar(grupo_com_bia.id, [ids["caio"]])
    pesquisas.entregar(grupo_com_bia.pesquisa.id)
    como("caio@x.com")
    convite = grupos.convites_pendentes(turma.id)[0]
    with pytest.raises(RegraViolada, match="foi entregue ao professor"):
        grupos.responder_convite(convite.id, True)
    grupos.responder_convite(convite.id, False)  # recusar continua possível


def test_integrantes_voltam_a_mudar_se_o_professor_devolve(grupo_com_bia, grupos, pesquisas, revisoes, cenario, como):
    _, ids = cenario
    pid = grupo_com_bia.pesquisa.id
    pesquisas.entregar(pid)
    como("prof@x.com", "professor")
    revisoes.devolver(pid, "ajuste")
    assert [a.nome for a in grupos.atribuir_aluno(grupo_com_bia.id, ids["caio"]).alunos] == ["Ana", "Bia", "Caio"]


# ---------------------------------------------------------------- professor atribui e remove
def test_professor_atribui_aluno_a_grupo_e_cria_a_pesquisa_se_preciso(grupo, grupos, cenario, como):
    _, ids = cenario
    como("prof@x.com", "professor")
    g = grupos.atribuir_aluno(grupo.id, ids["caio"])
    assert sorted(a.nome for a in g.alunos) == ["Ana", "Caio"]
    assert g.pesquisa is not None and g.pesquisa.titulo == "Impacto da IA"
    with pytest.raises(RegraViolada, match="já está no grupo"):
        grupos.atribuir_aluno(grupo.id, ids["caio"])


def test_professor_so_atribui_aluno_da_turma(grupo, grupos, como, cenario):
    como("dani@x.com")
    dani = sessao.usuario.id
    como("prof@x.com", "professor")
    with pytest.raises(RegraViolada, match="não faz parte da turma"):
        grupos.atribuir_aluno(grupo.id, dani)


def test_professor_remove_aluno_mas_nao_o_ultimo(grupo_com_bia, grupos, cenario, como):
    _, ids = cenario
    como("prof@x.com", "professor")
    g = grupos.remover_aluno(grupo_com_bia.id, ids["bia"])
    assert [a.nome for a in g.alunos] == ["Ana"] and g.pesquisa is not None  # a pesquisa continua
    with pytest.raises(RegraViolada, match="último integrante"):
        grupos.remover_aluno(grupo_com_bia.id, ids["ana"])
    with pytest.raises(RegraViolada, match="não está no grupo"):
        grupos.remover_aluno(grupo_com_bia.id, ids["bia"])
    como("bia@x.com")  # a Bia perdeu o acesso à pesquisa do grupo
    from services.pesquisa_service import PesquisaService

    with pytest.raises(RegraViolada, match="Pesquisa não encontrada"):
        PesquisaService().obter(g.pesquisa.id)


def test_gestao_de_grupo_e_so_do_professor_da_turma(grupo, grupos, cenario, como):
    _, ids = cenario
    como("bia@x.com")
    with pytest.raises(RegraViolada, match="exclusiva de professores"):
        grupos.atribuir_aluno(grupo.id, ids["bia"])
    como("outro@x.com", "professor")
    with pytest.raises(RegraViolada, match="Grupo não encontrado"):
        grupos.atribuir_aluno(grupo.id, ids["bia"])
    with pytest.raises(RegraViolada, match="Grupo não encontrado"):
        grupos.remover_aluno(grupo.id, ids["ana"])


def test_professor_ve_grupos_da_turma_com_integrantes(grupo_com_bia, turmas, cenario, como):
    turma, _ = cenario
    como("prof@x.com", "professor")
    t = turmas.obter_do_professor(turma.id)
    assert [g.nome for g in t.grupos] == ["Time A"]
    assert sorted(a.nome for a in t.grupos[0].alunos) == ["Ana", "Bia"]
    assert t.grupos[0].pesquisa.titulo == "Impacto da IA"
