"""Telas de turmas, grupos e convites, e a edição de fonte. Usam a mesma 'cena' de test_ui.py."""
import pytest

pytest.importorskip("PySide6")

from test_ui import Cena, app, cena  # noqa: E402,F401  (fixtures e a cena de test_ui.py)


def _tudo(widget):
    """Todo o texto de um diálogo, mesmo sem ele estar na tela (os testes não o exibem de verdade)."""
    from PySide6.QtWidgets import QLabel, QPushButton

    return "\n".join(
        [l.text() for l in widget.findChildren(QLabel)] + [b.text() for b in widget.findChildren(QPushButton)]
    )


def _linha_com(tela, texto, cena):
    for linha in tela.linhas:
        if texto in cena.textos(linha):
            return linha
    raise AssertionError(f"nenhuma linha com «{texto}»")


# ================================================================ aluno: turmas
def test_aluno_sem_turma_ve_a_orientacao_e_entra_pelo_codigo(cena):
    cena.cadastrar("Ana", "ana@x.com", "segredo1")
    cena.entrar("ana@x.com", "segredo1")
    t = cena.janela.tela_turmas
    assert cena.tela is t and t.linhas == []
    assert "ainda não entrou em nenhuma turma" in cena.textos(t)

    cena.garantir_turma_padrao()
    # código errado: o diálogo fica aberto e explica
    erros = []
    cena.dialogo({"codigo": "ZZZZZZ"}, depois=lambda d: erros.append(d.erro.text()))
    cena.clicar(t.botao_entrar)
    assert erros and "Não existe turma" in erros[0] and cena.tela is t

    cena.entrar_na_turma("  turma1 ")  # minúsculas e espaços: vale
    p = cena.janela.tela_pesquisas
    assert cena.tela is p and "Projeto 1" in cena.textos(p) and "Você entrou na turma Projeto 1" in cena.aviso
    cena.clicar(p.botao_voltar)
    assert [cena.textos(l) for l in t.linhas][0].startswith("Projeto 1")
    assert "Professor: Dono" in cena.textos(t.linhas[0])


def test_entrar_de_novo_na_mesma_turma_e_recusado(cena):
    cena.entrar_como_aluno()
    cena.clicar(cena.janela.tela_pesquisas.botao_voltar)
    erros = []
    cena.dialogo({"codigo": "TURMA1"}, depois=lambda d: erros.append(d.erro.text()))
    cena.clicar(cena.janela.tela_turmas.botao_entrar)
    assert erros and "já está nesta turma" in erros[0]


def test_pesquisa_nasce_dentro_da_turma_e_so_aparece_nela(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa("Da turma 1", "obj")
    cena.clicar(cena.janela.tela_pesquisa.botao_voltar)
    assert cena.janela.tela_pesquisas.turma.nome == "Projeto 1"
    assert [l.pesquisa_id for l in cena.janela.tela_pesquisas.linhas] == [cena.janela.tela_pesquisa.pesquisa_id]
    # outra turma, vazia
    from tests.apoio import turma_do_dono_escondido

    turma_do_dono_escondido("Banco de Dados", "BDADOS")
    cena.clicar(cena.janela.tela_pesquisas.botao_voltar)
    cena.entrar_na_turma("BDADOS")
    p = cena.janela.tela_pesquisas
    assert p.turma.nome == "Banco de Dados" and p.linhas == []
    assert "ainda não criou nenhuma pesquisa nesta turma" in cena.textos(p)
    # a voltar, as duas turmas aparecem
    cena.clicar(p.botao_voltar)
    assert len(cena.janela.tela_turmas.linhas) == 2


def test_turma_sem_grupos_deixa_grupos_e_convites_cinza(cena):
    cena.entrar_como_aluno()
    p = cena.janela.tela_pesquisas
    assert not p.aba_grupos.isEnabled() and not p.botao_convites.isEnabled()
    assert "não habilitou grupos" in p.aba_grupos.toolTip()
    assert p.aba_individuais.isEnabled()
    cena.janela.abrir_pesquisas(p.turma_id, "grupos")  # pedir a aba por número não adianta
    assert cena.janela.tela_pesquisas.visao == "individuais"
    assert not cena.janela.tela_pesquisas.botao_criar_grupo.isVisible()


def test_criar_grupo_so_aparece_na_aba_de_grupos(cena):
    cena.entrar_como_aluno(grupos=True)
    p = cena.janela.tela_pesquisas
    assert p.aba_grupos.isEnabled() and p.botao_convites.isEnabled()
    assert p.botao_nova.isVisible() and not p.botao_criar_grupo.isVisible()
    cena.clicar(p.aba_grupos)
    p = cena.janela.tela_pesquisas
    assert p.visao == "grupos" and p.botao_criar_grupo.isVisible() and not p.botao_nova.isVisible()
    assert "não faz parte de nenhum grupo" in cena.textos(p)
    cena.clicar(p.aba_individuais)
    p = cena.janela.tela_pesquisas
    assert p.botao_nova.isVisible() and not p.botao_criar_grupo.isVisible()


# ================================================================ grupos e convites
def _ana_cria_grupo_e_convida_bia(cena):
    """Bia e Ana entram na turma com grupos; Ana cria o grupo 'Time A' e convida a Bia."""
    cena.entrar_como_aluno("Bia", "bia@x.com", grupos=True)
    cena.sair()
    cena.entrar_como_aluno("Ana", "ana@x.com", grupos=True)
    cena.clicar(cena.janela.tela_pesquisas.aba_grupos)
    ids = {}

    def marcar_bia(d):
        assert [c.text() for c in d.caixas.values()] == ["Bia"]  # só a colega, não ela mesma
        d.marcar(*d.caixas.keys())

    cena.dialogo({"nome": "Time A", "titulo": "Impacto da IA", "objetivo": "Medir o impacto"})
    cena.dialogo(antes=marcar_bia)
    cena.clicar(cena.janela.tela_pesquisas.botao_criar_grupo)


def test_criar_grupo_convida_colegas_e_fica_aguardando(cena):
    _ana_cria_grupo_e_convida_bia(cena)
    p = cena.janela.tela_pesquisas
    assert "Convites enviados" in cena.aviso
    [linha] = p.linhas
    assert "Aguardando integrantes" in cena.textos(linha) and "1 convite pendente" in cena.textos(linha)
    assert "Time A" in cena.textos(linha) and "Ana" in cena.textos(linha)
    assert linha.botao_convidar is not None and linha.pesquisa_id is None
    assert cena.janela.tela_pesquisas.botao_convites.text() == "Convites"  # quem convidou não tem convite


def test_grupo_valida_os_campos_dentro_do_dialogo(cena):
    cena.entrar_como_aluno(grupos=True)
    cena.clicar(cena.janela.tela_pesquisas.aba_grupos)
    erros = []
    cena.dialogo({"nome": "", "titulo": "T", "objetivo": "O"}, depois=lambda d: erros.append(d.erro.text()))
    cena.clicar(cena.janela.tela_pesquisas.botao_criar_grupo)
    assert erros and "nome ao grupo" in erros[0]


def test_sem_colegas_o_grupo_nasce_e_avisa_que_nao_ha_quem_convidar(cena):
    cena.entrar_como_aluno(grupos=True)
    cena.clicar(cena.janela.tela_pesquisas.aba_grupos)
    cena.dialogo({"nome": "Solo", "titulo": "T", "objetivo": "O"})
    cena.clicar(cena.janela.tela_pesquisas.botao_criar_grupo)
    assert "Ainda não há outros alunos" in cena.aviso
    assert len(cena.janela.tela_pesquisas.linhas) == 1


def test_bia_aceita_o_convite_e_a_pesquisa_do_grupo_nasce(cena):
    _ana_cria_grupo_e_convida_bia(cena)
    cena.sair()
    cena.entrar_de_novo("bia@x.com")
    cena.clicar(cena.janela.tela_turmas.linhas[0])
    p = cena.janela.tela_pesquisas
    assert p.botao_convites.text() == "Convites (1)"

    def aceitar(d):
        [item] = d.itens
        assert "Time A" in _tudo(item) and "Ana convidou você" in _tudo(item)
        item.botao_aceitar.click()
        assert d.itens == [] and not d.vazio.isHidden()

    cena.dialogo(antes=aceitar)
    cena.clicar(p.botao_convites)
    p = cena.janela.tela_pesquisas
    assert p.visao == "grupos" and "Você entrou no grupo Time A" in cena.aviso
    [linha] = p.linhas
    assert "Impacto da IA" in cena.textos(linha) and "Ana e Bia" in cena.textos(linha)
    assert "Em andamento" in linha.selo.text() and linha.pesquisa_id is not None
    assert p.botao_convites.text() == "Convites"

    # a pesquisa do grupo: mostra o grupo, sem botão de excluir, com convidar
    cena.clicar(linha)
    t = cena.janela.tela_pesquisa
    assert "Grupo Time A" in t.integrantes.text() and "Ana e Bia" in t.integrantes.text()
    assert t.botao_convidar.isVisible() and not t.botao_excluir.isVisible()
    cena.registrar_interacao("Claude", "Pergunta da Bia", "Resposta.")
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    cena.clicar(cena.janela.tela_pesquisa.botao_voltar)
    assert cena.janela.tela_pesquisas.visao == "grupos"  # voltou para a aba de onde veio
    cena.sair()

    # Ana enxerga a mesma pesquisa, com a interação da Bia
    cena.entrar_de_novo("ana@x.com")
    cena.clicar(cena.janela.tela_turmas.linhas[0])
    cena.clicar(cena.janela.tela_pesquisas.aba_grupos)
    [linha] = cena.janela.tela_pesquisas.linhas
    cena.clicar(linha)
    t = cena.janela.tela_pesquisa
    assert [l.interacao_id for l in t.linhas] and "Pergunta da Bia" in cena.textos(t.linhas[0])
    # a pesquisa de grupo não aparece nas individuais
    cena.clicar(t.botao_voltar)
    cena.clicar(cena.janela.tela_pesquisas.aba_individuais)
    assert cena.janela.tela_pesquisas.linhas == []


def test_recusar_o_convite_nao_cria_pesquisa(cena):
    _ana_cria_grupo_e_convida_bia(cena)
    cena.sair()
    cena.entrar_de_novo("bia@x.com")
    cena.clicar(cena.janela.tela_turmas.linhas[0])
    cena.dialogo(antes=lambda d: d.itens[0].botao_recusar.click())
    cena.clicar(cena.janela.tela_pesquisas.botao_convites)
    p = cena.janela.tela_pesquisas
    assert "Convite recusado" in cena.aviso and p.botao_convites.text() == "Convites" and p.visao == "individuais"
    cena.clicar(p.aba_grupos)
    assert cena.janela.tela_pesquisas.linhas == []
    # sem convites pendentes o diálogo diz isso
    vistos = []
    cena.dialogo(antes=lambda d: vistos.append("Nenhum convite pendente" in _tudo(d)))
    cena.clicar(cena.janela.tela_pesquisas.botao_convites)
    assert vistos == [True]


def test_convidar_mais_alunos_pela_tela_da_pesquisa_do_grupo(cena):
    _ana_cria_grupo_e_convida_bia(cena)
    cena.sair()
    cena.entrar_como_aluno("Caio", "caio@x.com", grupos=True)
    cena.sair()
    cena.entrar_de_novo("bia@x.com")
    cena.clicar(cena.janela.tela_turmas.linhas[0])
    cena.dialogo(antes=lambda d: d.itens[0].botao_aceitar.click())
    cena.clicar(cena.janela.tela_pesquisas.botao_convites)
    cena.clicar(cena.janela.tela_pesquisas.linhas[0])
    t = cena.janela.tela_pesquisa

    def so_o_caio(d):
        assert [c.text() for c in d.caixas.values()] == ["Caio"]
        d.marcar(*d.caixas.keys())

    cena.dialogo(antes=so_o_caio)
    cena.clicar(t.botao_convidar)
    assert "Convites enviados" in cena.aviso
    # agora não sobra ninguém para convidar
    cena.clicar(cena.janela.tela_pesquisa.botao_convidar)
    assert "Não há mais colegas" in cena.aviso


def test_pesquisa_de_grupo_entregue_trava_e_o_professor_ve_o_grupo(cena):
    _ana_cria_grupo_e_convida_bia(cena)
    cena.sair()
    cena.entrar_de_novo("bia@x.com")
    cena.clicar(cena.janela.tela_turmas.linhas[0])
    cena.dialogo(antes=lambda d: d.itens[0].botao_aceitar.click())
    cena.clicar(cena.janela.tela_pesquisas.botao_convites)
    cena.clicar(cena.janela.tela_pesquisas.linhas[0])
    cena.registrar_interacao()
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    cena.entregar()
    t = cena.janela.tela_pesquisa
    assert t.pesquisa.status == "entregue" and not t.botao_convidar.isVisible()
    cena.sair()

    cena.entrar_como_professor()
    p = cena.janela.tela_professor
    [linha] = p.secoes["entregue"]
    assert "Grupo Time A (Ana e Bia)" in cena.textos(linha) and "Projeto 1" in cena.textos(linha)
    cena.clicar(linha)
    rev = cena.janela.tela_revisao
    assert "Grupo Time A" in rev.autor.text() and "Ana e Bia" in rev.autor.text()
    assert rev.botao_voltar.text() == "‹ Projeto 1"
    cena.clicar(rev.botao_relatorio)
    texto = cena.janela.tela_relatorio.texto()
    assert "Integrantes" in texto and "Ana, Bia" in texto and "Time A" in texto and "Projeto 1" in texto


# ================================================================ professor: turmas
def test_professor_cria_turma_com_codigo_e_a_exclui(cena):
    cena.cadastrar("Profa", "prof@x.com", "segredo1", "professor")
    cena.entrar("prof@x.com", "segredo1")
    t = cena.janela.tela_turmas_professor
    assert cena.tela is t and "ainda não criou nenhuma turma" in cena.textos(t)

    erros = []
    cena.dialogo({"nome": "  "}, depois=lambda d: erros.append(d.erro.text()))
    cena.clicar(t.botao_nova)
    assert erros and "nome da turma" in erros[0]

    cena.dialogo({"nome": "Projeto 1, SI 26.2", "permite_grupos": True})
    cena.clicar(t.botao_nova)
    tt = cena.janela.tela_turma_professor
    assert cena.tela is tt and tt.turma.permite_grupos
    codigo = tt.turma.codigo
    assert len(codigo) == 6 and tt.codigo.text() == codigo and f"Código de entrada: {codigo}" in cena.aviso
    assert "Grupos permitidos" in tt.selo_grupos.text() and tt.aba_grupos.isEnabled()
    assert "Nenhum aluno entrou ainda" in cena.textos(tt) and codigo in cena.textos(tt)

    cena.clicar(tt.botao_voltar)
    [linha] = t.linhas if False else cena.janela.tela_turmas_professor.linhas
    assert linha.codigo.text() == codigo and "0 alunos" in cena.textos(linha) and "Grupos permitidos" in linha.selo.text()
    cena.clicar(linha.botao_copiar)
    from PySide6.QtGui import QGuiApplication

    assert QGuiApplication.clipboard().text() == codigo and "copiado" in cena.aviso

    # excluir pede confirmação
    cena.responder(False)
    cena.clicar(linha.botao_excluir)
    assert "Excluir esta turma?" == cena.perguntas[-1][0] and len(cena.janela.tela_turmas_professor.linhas) == 1
    cena.responder(True)
    cena.clicar(linha.botao_excluir)
    assert cena.janela.tela_turmas_professor.linhas == [] and "Turma excluída" in cena.aviso


def test_turma_criada_sem_grupos_deixa_a_aba_de_grupos_cinza(cena):
    cena.cadastrar("Profa", "prof@x.com", "segredo1", "professor")
    cena.entrar("prof@x.com", "segredo1")
    cena.dialogo({"nome": "Cálculo", "permite_grupos": False})
    cena.clicar(cena.janela.tela_turmas_professor.botao_nova)
    tt = cena.janela.tela_turma_professor
    assert not tt.aba_grupos.isEnabled() and "Grupos desativados" in tt.selo_grupos.text()
    cena.janela.abrir_turma_professor(tt.turma_id, "grupos")
    assert cena.janela.tela_turma_professor.visao == "alunos"


def test_aluno_entra_com_o_codigo_gerado_pelo_professor_na_tela(cena):
    cena.cadastrar("Profa", "prof@x.com", "segredo1", "professor")
    cena.entrar("prof@x.com", "segredo1")
    cena.dialogo({"nome": "Redes", "permite_grupos": False})
    cena.clicar(cena.janela.tela_turmas_professor.botao_nova)
    codigo = cena.janela.tela_turma_professor.turma.codigo
    cena.sair()
    cena.cadastrar("Ana", "ana@x.com", "segredo1")
    cena.entrar("ana@x.com", "segredo1")
    cena.entrar_na_turma(codigo)
    p = cena.janela.tela_pesquisas
    assert p.turma.nome == "Redes" and "Professor: Profa" in cena.textos(p)


def test_professor_ve_alunos_com_as_pesquisas_de_cada_um(cena):
    cena.entrar_como_aluno("Bia", "bia@x.com")
    cena.criar_pesquisa("Pesquisa da Bia")
    cena.sair()
    cena.entrar_como_aluno("Ana", "ana@x.com")
    cena.criar_pesquisa("Primeira da Ana")
    cena.clicar(cena.janela.tela_pesquisa.botao_voltar)
    cena.criar_pesquisa("Segunda da Ana")
    cena.entregar()
    cena.sair()
    cena.entrar_como_aluno("Caio", "caio@x.com")  # sem pesquisa
    cena.sair()

    cena.entrar_como_professor(lista=False)
    cena.clicar(cena.janela.tela_turmas_professor.linhas[0])
    tt = cena.janela.tela_turma_professor
    assert [b.cabecalho.text() for b in tt.blocos] == [
        "Ana  (2 pesquisas)", "Bia  (1 pesquisa)", "Caio  (0 pesquisas)"
    ]
    ana, bia, caio = tt.blocos
    assert len(ana.linhas) == 2 and len(bia.linhas) == 1 and caio.linhas == []
    assert "Ainda não criou pesquisa individual" in cena.textos(caio)
    titulos = [cena.textos(l) for l in ana.linhas]
    assert "Segunda da Ana" in titulos[0] and "Aguardando sua revisão" in titulos[0]  # a entregue vem primeiro
    # o botão do relatório só abre a entregue
    assert ana.linhas[0].botao_relatorio.isEnabled() and not ana.linhas[1].botao_relatorio.isEnabled()
    cena.clicar(ana.linhas[0])
    assert cena.janela.tela_revisao.pesquisa.titulo == "Segunda da Ana"
    cena.clicar(cena.janela.tela_revisao.botao_voltar)
    assert cena.tela is cena.janela.tela_turma_professor  # volta para a turma, não para uma lista solta


def test_lista_de_pesquisas_do_professor_filtra_por_turma(cena):
    cena.entrar_como_aluno("Ana", "ana@x.com")
    cena.criar_pesquisa("Na Projeto 1")
    cena.clicar(cena.janela.tela_pesquisa.botao_voltar)
    from tests.apoio import passar_turmas_para, turma_do_dono_escondido

    turma_do_dono_escondido("Banco de Dados", "BDADOS")
    cena.clicar(cena.janela.tela_pesquisas.botao_voltar)
    cena.entrar_na_turma("BDADOS")
    cena.criar_pesquisa("Em Banco de Dados")
    cena.sair()
    cena.cadastrar("Profa", "prof@x.com", "segredo1", "professor")
    cena.entrar("prof@x.com", "segredo1")
    passar_turmas_para("prof@x.com")
    cena.clicar(cena.janela.tela_turmas_professor.botao_pesquisas)
    p = cena.janela.tela_professor
    assert [i for i in range(p.filtro.count())] == [0, 1, 2] and p.filtro.itemText(0) == "Todas as turmas"
    assert len(p.linhas) == 2 and "Projeto 1" in cena.textos(_linha_com(p, "Na Projeto 1", cena))
    p.filtro.setCurrentIndex(p.filtro.findText("Banco de Dados"))
    cena.app.processEvents()
    p = cena.janela.tela_professor
    assert p.turma_id is not None and [cena.textos(l).split("\n")[0] for l in p.linhas] == ["Em Banco de Dados"]
    p.filtro.setCurrentIndex(0)
    assert len(cena.janela.tela_professor.linhas) == 2
    # só vê pesquisas das próprias turmas: uma turma de outro professor não entra no filtro
    assert p.turma_id is None


def test_professor_remove_e_atribui_alunos_em_grupos(cena):
    _ana_cria_grupo_e_convida_bia(cena)
    cena.sair()
    cena.entrar_de_novo("bia@x.com")
    cena.clicar(cena.janela.tela_turmas.linhas[0])
    cena.dialogo(antes=lambda d: d.itens[0].botao_aceitar.click())
    cena.clicar(cena.janela.tela_pesquisas.botao_convites)
    cena.sair()
    cena.entrar_como_aluno("Caio", "caio@x.com", grupos=True)
    cena.sair()

    cena.entrar_como_professor(lista=False)
    cena.clicar(cena.janela.tela_turmas_professor.linhas[0])
    tt = cena.janela.tela_turma_professor
    cena.clicar(tt.aba_grupos)
    tt = cena.janela.tela_turma_professor
    assert tt.visao == "grupos" and "Alunos sem grupo: Caio" in tt.sem_grupo.text()
    [grupo] = tt.blocos
    assert "Time A" in grupo.cabecalho.text() and len(grupo.integrantes) == 2 and len(grupo.linhas) == 1

    # atribuir o Caio
    def escolher_caio(d):
        assert [d.combo.itemText(i) for i in range(d.combo.count())] == ["Caio"]

    cena.dialogo(antes=escolher_caio)
    cena.clicar(grupo.botao_atribuir)
    tt = cena.janela.tela_turma_professor
    assert "Aluno atribuído" in cena.aviso and tt.sem_grupo is None
    [grupo] = tt.blocos
    assert len(grupo.integrantes) == 3

    # remover a Bia (com confirmação)
    bia_id = next(a.id for a in tt.turma.alunos if a.nome == "Bia")
    cena.responder(False)
    cena.clicar(grupo.integrantes[bia_id])
    assert "Remover aluno do grupo?" == cena.perguntas[-1][0] and len(grupo.integrantes) == 3
    cena.responder(True)
    cena.clicar(grupo.integrantes[bia_id])
    tt = cena.janela.tela_turma_professor
    assert "Bia foi removido" in cena.aviso and "Alunos sem grupo: Bia" in tt.sem_grupo.text()
    assert len(tt.blocos[0].integrantes) == 2
    # a aba Alunos mostra os grupos de cada um
    cena.clicar(tt.aba_alunos)
    por_nome = {b.cabecalho.text().split("  ")[0]: b for b in cena.janela.tela_turma_professor.blocos}
    assert por_nome["Caio"].grupos.text() == "Em grupos: Time A" and por_nome["Bia"].grupos is None


def test_professor_nao_remove_o_ultimo_integrante_do_grupo(cena):
    cena.entrar_como_aluno("Ana", "ana@x.com", grupos=True)
    cena.clicar(cena.janela.tela_pesquisas.aba_grupos)
    cena.dialogo({"nome": "Solo", "titulo": "T", "objetivo": "O"})
    cena.clicar(cena.janela.tela_pesquisas.botao_criar_grupo)
    cena.sair()
    cena.entrar_como_professor(lista=False)
    cena.clicar(cena.janela.tela_turmas_professor.linhas[0])
    cena.clicar(cena.janela.tela_turma_professor.aba_grupos)
    [grupo] = cena.janela.tela_turma_professor.blocos
    assert "Ainda sem pesquisa" in cena.textos(grupo)
    cena.responder(True)
    cena.clicar(next(iter(grupo.integrantes.values())))
    assert "último integrante" in cena.aviso


def test_turma_do_professor_mostra_aguardando_revisao_na_lista(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.entregar()
    cena.sair()
    cena.entrar_como_professor(lista=False)
    [linha] = cena.janela.tela_turmas_professor.linhas
    assert "1 aluno" in cena.textos(linha) and "1 pesquisa" in cena.textos(linha)
    assert "1 aguardando revisão" in linha.aguardando.text()


# ================================================================ editar fonte
def test_aluno_edita_referencia_e_link_da_fonte(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva 2023", "http://velho.com")
    cartao = cena.cartao("Silva 2023")
    assert cartao.botao_editar.isVisible()
    avisos = []
    cena.dialogo(
        {"referencia": "SILVA, J. A educação na era da IA. 2023.", "link": "https://novo.com/artigo"},
        antes=lambda d: avisos.append(d.campos["referencia"].toPlainText()),
    )
    cena.clicar(cartao.botao_editar)
    assert avisos == ["Silva 2023"]  # o formulário abre com a referência atual
    novo = cena.cartao("SILVA, J. A educação na era da IA. 2023.")
    assert "novo.com/artigo" in novo.link.text() and "Fonte atualizada" in cena.aviso


def test_editar_fonte_verificada_avisa_e_ela_volta_a_nao_verificada(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva 2023")
    cena.verificacao("verificada", "achei", "meu trecho")
    cena.clicar(cena.cartao("Silva 2023").botao_verificar)
    assert "Verificada" in cena.cartao("Silva 2023").selo.text()
    subtitulos = []
    cena.dialogo({"referencia": "Silva 2024"}, antes=lambda d: subtitulos.append(_tudo(d)))
    cena.clicar(cena.cartao("Silva 2023").botao_editar)
    assert "volta a" in subtitulos[0] and "trechos ligados" in subtitulos[0]
    novo = cena.cartao("Silva 2024")
    assert "Não verificada" in novo.selo.text() and novo.trechos == []
    assert "voltou a “não verificada”" in cena.aviso


def test_editar_fonte_exige_referencia_dentro_do_dialogo(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva 2023")
    erros = []
    cena.dialogo({"referencia": "  "}, depois=lambda d: erros.append(d.erro.text()))
    cena.clicar(cena.cartao("Silva 2023").botao_editar)
    assert erros and "referência" in erros[0]
    assert cena.cartao("Silva 2023")  # nada mudou


def test_fonte_de_pesquisa_entregue_nao_mostra_editar(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva 2023")
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    cena.entregar()
    cena.clicar(cena.janela.tela_pesquisa.linhas[0])
    assert not cena.cartao("Silva 2023").botao_editar.isVisible()


# ================================================================ tutoriais novos
def test_tutoriais_das_telas_novas(cena):
    j = cena.janela
    cena.cadastrar("Ana", "ana@x.com", "segredo1")
    cena.entrar("ana@x.com", "segredo1")
    cena.fechar_tutorial("aluno_turmas")
    cena.clicar(j.tela_turmas.botao_tutorial)
    cena.sair()
    cena.cadastrar("Profa", "prof@x.com", "segredo1", "professor")
    cena.entrar("prof@x.com", "segredo1")
    cena.fechar_tutorial("prof_turmas")
    cena.clicar(j.tela_turmas_professor.botao_tutorial)
    cena.dialogo({"nome": "Redes", "permite_grupos": True})
    cena.clicar(j.tela_turmas_professor.botao_nova)
    cena.fechar_tutorial("prof_turma")
    cena.clicar(j.tela_turma_professor.botao_tutorial)
    cena.janela.abrir_professor()
    cena.fechar_tutorial("prof_lista")
    cena.clicar(j.tela_professor.botao_tutorial)


def test_filtro_de_turma_e_legivel_mesmo_com_paleta_escura_do_sistema(cena):
    """Bug: no modo escuro do Windows a lista suspensa do filtro ficava escura e ilegível.
    Simula a paleta escura do sistema e confere que o campo e a lista abertos continuam claros."""
    from PySide6.QtGui import QColor, QPalette

    from ui import estilo

    cena.entrar_como_aluno("Ana", "ana@x.com")
    cena.criar_pesquisa("Qualquer")
    cena.sair()
    escura = QPalette()
    for papel in (QPalette.Window, QPalette.Base, QPalette.Button, QPalette.AlternateBase):
        escura.setColor(papel, QColor("#1e1e1e"))
    for papel in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        escura.setColor(papel, QColor("#ffffff"))
    cena.app.setPalette(escura)  # o sistema está no modo escuro...
    estilo.aplicar(cena.app)  # ...e o programa aplica o próprio estilo por cima, como ao abrir
    cena.entrar_como_professor()
    filtro = cena.janela.tela_professor.filtro

    def claro(imagem):
        pixels = [QColor(imagem.pixel(x, y)).lightness() for x in range(2, imagem.width() - 2, 2)
                  for y in range(2, imagem.height() - 2, 2)]
        return sorted(pixels)[len(pixels) // 2]  # o tom mais comum (o fundo), não o texto fino

    assert claro(filtro.grab().toImage()) > 200  # o campo fechado é claro
    filtro.showPopup()
    cena.app.processEvents()
    assert claro(filtro.view().viewport().grab().toImage()) > 200  # a lista aberta também
    filtro.hidePopup()
