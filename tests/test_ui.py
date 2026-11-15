"""Testes das telas (PySide6): a janela é aberta de verdade (sem aparecer no monitor) e os testes
digitam nos campos, clicam em botões e linhas, como um usuário. Os serviços e o banco são os reais.

Os diálogos (formulários) e as perguntas de confirmação normalmente prendem o teste esperando
alguém clicar; aqui eles são respondidos por um roteiro combinado antes do clique.
"""
import sys

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt, qInstallMessageHandler  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QPushButton  # noqa: E402

from ui import componentes, estilo  # noqa: E402
from ui.dialogos import DialogoVerificacao  # noqa: E402
from ui.janela_principal import JanelaPrincipal  # noqa: E402
from ui.tela_relatorio import exportar_pdf  # noqa: E402


@pytest.fixture(scope="session")
def app():
    aplicativo = QApplication.instance() or QApplication([])
    estilo.aplicar(aplicativo)
    return aplicativo


class Cena:
    """A janela aberta mais as ferramentas para agir sobre ela."""

    def __init__(self, janela, app):
        self.janela = janela
        self.app = app
        self.roteiros = []   # o que fazer em cada diálogo que abrir, na ordem
        self.respostas = []  # respostas (True/False) às perguntas de confirmação
        self.perguntas = []  # textos das perguntas feitas
        self.arquivo_pdf = ""

    # ---------------------------------------------------------------- ver
    @property
    def tela(self):
        return self.janela.pilha.currentWidget()

    def textos(self, widget=None):
        """Todo o texto visível de uma tela (ou da janela inteira), um rótulo por linha."""
        raiz = widget or self.janela
        partes = [r.text() for r in raiz.findChildren(QLabel) if r.isVisible()]
        partes += [b.text() for b in raiz.findChildren(QPushButton) if b.isVisible()]
        return "\n".join(partes)

    @property
    def aviso(self):
        f = self.janela.faixa_aviso
        return f.text() if f.isVisible() else ""

    # ---------------------------------------------------------------- agir
    def clicar(self, widget):
        assert widget.isVisible(), f"o botão/linha não está visível: {getattr(widget, 'text', lambda: widget)()}"
        assert widget.isEnabled()
        QTest.mouseClick(widget, Qt.LeftButton)
        self.app.processEvents()

    def digitar(self, campo, texto):
        campo.clear()
        QTest.keyClicks(campo, texto)

    def dialogo(self, valores=None, clicar="ok", antes=None, depois=None):
        """Combina o que fazer no próximo formulário: preencher e clicar em OK (ou Cancelar)."""

        def roteiro(d):
            if antes:
                antes(d)
            if valores:
                d.definir(**valores)
            getattr(d, f"botao_{clicar}").click()
            if d.result() == 0 and depois:  # ficou aberto: o service recusou
                depois(d)
                d.reject()

        self.roteiros.append(roteiro)

    def verificacao(self, resultado, anotacao="", trecho="", localizacao="", antes=None, depois=None):
        def roteiro(d):
            assert isinstance(d, DialogoVerificacao)
            if antes:
                antes(d)
            d.opcoes[resultado].setChecked(True)
            d.anotacao.setPlainText(anotacao)
            if d.trecho.isEnabled():
                d.trecho.setPlainText(trecho)
                d.localizacao.setText(localizacao)
            d.botao_ok.click()
            if d.result() == 0 and depois:
                depois(d)
                d.reject()

        self.roteiros.append(roteiro)

    def responder(self, *respostas):
        self.respostas.extend(respostas)

    # ---------------------------------------------------------------- atalhos do fluxo
    def cadastrar(self, nome, email, senha, tipo="aluno"):
        a = self.janela.tela_acesso
        self.clicar(a.botao_ir_cadastro)
        self.digitar(a.cad_nome, nome)
        self.digitar(a.cad_email, email)
        self.digitar(a.cad_senha, senha)
        (a.radio_aluno if tipo == "aluno" else a.radio_professor).setChecked(True)
        self.clicar(a.botao_criar_conta)

    def entrar(self, email, senha):
        a = self.janela.tela_acesso
        self.digitar(a.login_email, email)
        self.digitar(a.login_senha, senha)
        self.clicar(a.botao_entrar)

    def sair(self):
        self.clicar(self.janela.botao_sair)

    def entrar_como_aluno(self, nome="Ana", email="ana@x.com", senha="segredo1"):
        self.cadastrar(nome, email, senha)
        self.entrar(email, senha)
        assert self.tela is self.janela.tela_pesquisas

    def entrar_como_professor(self, nome="Profa", email="prof@x.com", senha="segredo1"):
        self.cadastrar(nome, email, senha, "professor")
        self.entrar(email, senha)
        assert self.tela is self.janela.tela_professor

    def criar_pesquisa(self, titulo="Impacto da IA", objetivo="Entender o uso de IA"):
        self.dialogo({"titulo": titulo, "objetivo": objetivo})
        self.clicar(self.janela.tela_pesquisas.botao_nova)
        assert self.tela is self.janela.tela_pesquisa

    def registrar_interacao(self, ferramenta="ChatGPT", pergunta="Qual o efeito da IA?", resposta="Grande."):
        self.dialogo({"ferramenta": ferramenta, "pergunta": pergunta, "resposta": resposta})
        self.clicar(self.janela.tela_pesquisa.botao_nova_interacao)
        assert self.tela is self.janela.tela_interacao

    def adicionar_fonte(self, referencia, link=""):
        self.dialogo({"referencia": referencia, "link": link})
        self.clicar(self.janela.tela_interacao.botao_adicionar_fonte)

    def cartao(self, referencia):
        for cartao in self.janela.tela_interacao.cartoes:
            if cartao.referencia.text() == referencia:
                return cartao
        raise AssertionError(f"fonte não encontrada na tela: {referencia}")


@pytest.fixture
def cena(app, monkeypatch, tmp_path):
    erros_em_slots = []
    monkeypatch.setattr(sys, "excepthook", lambda *args: erros_em_slots.append(args))
    componentes.ERROS_INESPERADOS.clear()

    janela = JanelaPrincipal()
    janela.show()
    app.processEvents()
    c = Cena(janela, app)

    def abrir_falso(dialogo):
        assert c.roteiros, f"abriu um diálogo sem roteiro: {dialogo.windowTitle()}"
        c.roteiros.pop(0)(dialogo)
        return dialogo.result()

    def perguntar_falso(parent, titulo, texto, rotulo_ok="Confirmar", perigo=False):
        c.perguntas.append((titulo, texto))
        assert c.respostas, f"fez uma pergunta sem resposta combinada: {titulo}"
        return c.respostas.pop(0)

    def arquivo_falso(parent, sugestao):
        return c.arquivo_pdf

    monkeypatch.setattr(componentes, "abrir", abrir_falso)
    monkeypatch.setattr(componentes, "perguntar", perguntar_falso)
    monkeypatch.setattr(componentes, "escolher_arquivo_pdf", arquivo_falso)
    c.tmp = tmp_path
    yield c
    # nenhuma tela pode ter escondido um erro inesperado, e nada pode sobrar no roteiro
    assert not erros_em_slots, f"exceção dentro de um slot do Qt: {erros_em_slots[:1]}"
    assert not componentes.ERROS_INESPERADOS, f"erro inesperado: {componentes.ERROS_INESPERADOS[:1]}"
    assert not c.roteiros, "sobrou diálogo combinado que nunca abriu"
    assert not c.respostas, "sobrou resposta combinada que nunca foi pedida"
    janela.close()


# ================================================================ acesso (RF01, RF02)
def test_a_janela_abre_na_tela_de_acesso_sem_ninguem_logado(cena):
    assert cena.tela is cena.janela.tela_acesso
    assert not cena.janela.botao_sair.isVisible()
    assert "Entrar" in cena.textos(cena.tela)


def test_criar_conta_e_entrar_pela_tela(cena):
    cena.cadastrar("Ana", "ANA@x.com", "segredo1")
    a = cena.janela.tela_acesso
    assert a.paginas.currentIndex() == 0  # voltou para o login
    assert a.login_email.text() == "ana@x.com"  # e-mail já preenchido, em minúsculas
    assert "Conta criada" in a.login_mensagem.text()

    cena.digitar(a.login_senha, "segredo1")
    cena.clicar(a.botao_entrar)
    assert cena.tela is cena.janela.tela_pesquisas
    assert "Ana · Aluno" in cena.janela.rotulo_usuario.text()


def test_enter_no_campo_de_senha_tambem_entra(cena):
    cena.cadastrar("Ana", "ana@x.com", "segredo1")
    a = cena.janela.tela_acesso
    cena.digitar(a.login_senha, "segredo1")
    QTest.keyClick(a.login_senha, Qt.Key_Return)
    assert cena.tela is cena.janela.tela_pesquisas


def test_login_errado_mostra_o_motivo_e_nao_entra(cena):
    cena.cadastrar("Ana", "ana@x.com", "segredo1")
    cena.entrar("ana@x.com", "errada")
    a = cena.janela.tela_acesso
    assert cena.tela is a
    assert a.login_mensagem.isVisible() and "incorretos" in a.login_mensagem.text()
    cena.entrar("quem@x.com", "segredo1")
    assert "incorretos" in a.login_mensagem.text()


def test_cadastro_recusado_mostra_o_motivo_na_tela(cena):
    a = cena.janela.tela_acesso
    cena.cadastrar("", "ana@x.com", "segredo1")
    assert a.paginas.currentIndex() == 1 and "nome" in a.cad_mensagem.text()
    cena.digitar(a.cad_nome, "Ana")
    cena.digitar(a.cad_senha, "123")
    cena.clicar(a.botao_criar_conta)
    assert "senha" in a.cad_mensagem.text()
    cena.digitar(a.cad_senha, "segredo1")
    cena.clicar(a.botao_criar_conta)  # agora dá certo
    cena.clicar(a.botao_ir_cadastro)
    cena.digitar(a.cad_nome, "Outra")
    cena.digitar(a.cad_email, "ANA@x.com")
    cena.digitar(a.cad_senha, "segredo1")
    cena.clicar(a.botao_criar_conta)
    assert "xiste uma conta" in a.cad_mensagem.text()


def test_sair_volta_ao_acesso_e_limpa_os_campos(cena):
    cena.entrar_como_aluno()
    cena.sair()
    a = cena.janela.tela_acesso
    assert cena.tela is a and a.login_email.text() == "" and a.login_senha.text() == ""
    assert not cena.janela.botao_sair.isVisible()
    assert "saiu da conta" in cena.aviso


# ================================================================ pesquisas (RF06, RF07, RF08)
def test_lista_vazia_convida_a_criar_a_primeira_pesquisa(cena):
    cena.entrar_como_aluno()
    assert "ainda não criou nenhuma pesquisa" in cena.textos(cena.tela)


def test_criar_pesquisa_abre_a_pesquisa_nova(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa("  Impacto da IA  ", "Entender")
    t = cena.janela.tela_pesquisa
    assert t.titulo.text() == "Impacto da IA"
    assert "Em andamento" in t.selo.text()
    assert "Pesquisa criada" in cena.aviso


def test_criar_pesquisa_sem_titulo_mostra_o_erro_no_formulario(cena):
    cena.entrar_como_aluno()
    vistos = []
    cena.dialogo({"titulo": " ", "objetivo": "O"}, depois=lambda d: vistos.append(d.erro.text()))
    cena.clicar(cena.janela.tela_pesquisas.botao_nova)
    assert vistos and "título" in vistos[0]
    assert cena.tela is cena.janela.tela_pesquisas  # nada foi criado


def test_cancelar_o_formulario_nao_cria_nada(cena):
    cena.entrar_como_aluno()
    cena.dialogo({"titulo": "X", "objetivo": "Y"}, clicar="cancelar")
    cena.clicar(cena.janela.tela_pesquisas.botao_nova)
    assert cena.tela is cena.janela.tela_pesquisas
    assert cena.janela.tela_pesquisas.linhas == []


def test_lista_mostra_so_as_pesquisas_do_aluno_e_abre_ao_clicar(cena):
    cena.entrar_como_aluno("Ana", "ana@x.com")
    cena.criar_pesquisa("Da Ana", "O")
    cena.sair()
    cena.entrar_como_aluno("Bia", "bia@x.com")
    assert cena.janela.tela_pesquisas.linhas == []
    cena.criar_pesquisa("Da Bia", "O")
    cena.clicar(cena.janela.tela_pesquisa.botao_voltar)
    linhas = cena.janela.tela_pesquisas.linhas
    assert len(linhas) == 1 and "Da Bia" in cena.textos(linhas[0])
    cena.clicar(linhas[0])
    assert cena.tela is cena.janela.tela_pesquisa
    assert cena.janela.tela_pesquisa.titulo.text() == "Da Bia"


def test_editar_pesquisa_pela_tela(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa("Tema", "Objetivo")
    cena.dialogo(
        {"titulo": "Tema novo", "objetivo": "Objetivo novo"},
        antes=lambda d: d.valores() == {"titulo": "Tema", "objetivo": "Objetivo"} or pytest.fail("não veio preenchido"),
    )
    cena.clicar(cena.janela.tela_pesquisa.botao_editar)
    assert cena.janela.tela_pesquisa.titulo.text() == "Tema novo"
    assert "Pesquisa atualizada" in cena.aviso


# ================================================================ interações (RF11, RF12, RF13, RF14)
def test_registrar_interacao_e_listar_na_pesquisa(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    assert "Nenhuma interação registrada ainda" in cena.textos(cena.tela)
    cena.registrar_interacao("Claude", "Primeira pergunta", "Primeira resposta")
    assert "Interação com Claude" in cena.textos(cena.tela)
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    cena.registrar_interacao("Gemini", "Segunda pergunta", "Segunda resposta")
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    linhas = cena.janela.tela_pesquisa.linhas
    assert len(linhas) == 2
    assert "Claude" in cena.textos(linhas[0]) and "Primeira pergunta" in cena.textos(linhas[0])
    assert "Gemini" in cena.textos(linhas[1])
    assert "Nenhuma fonte" in cena.textos(linhas[0])


def test_interacao_incompleta_nao_e_salva(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    vistos = []
    cena.dialogo({"ferramenta": "", "pergunta": "q", "resposta": "r"}, depois=lambda d: vistos.append(d.erro.text()))
    cena.clicar(cena.janela.tela_pesquisa.botao_nova_interacao)
    assert vistos and "ferramenta" in vistos[0]
    assert cena.janela.tela_pesquisa.linhas == []


def test_editar_interacao_mantem_as_fontes(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    cena.dialogo({"ferramenta": "Claude", "pergunta": "Pergunta corrigida", "resposta": "Grande."})
    cena.clicar(cena.janela.tela_interacao.botao_editar)
    t = cena.janela.tela_interacao
    assert "Interação com Claude" in t.titulo.text()
    assert t.painel_pergunta.texto.text() == "Pergunta corrigida"
    assert [c.referencia.text() for c in t.cartoes] == ["Silva (2023)"]
    assert "Interação atualizada" in cena.aviso


def test_excluir_interacao_pede_confirmacao_e_leva_fontes_junto(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    cena.responder(False)  # desiste
    cena.clicar(cena.janela.tela_interacao.botao_excluir)
    assert cena.tela is cena.janela.tela_interacao
    assert "1 fonte cadastrada" in cena.perguntas[-1][1]
    cena.responder(True)
    cena.clicar(cena.janela.tela_interacao.botao_excluir)
    assert cena.tela is cena.janela.tela_pesquisa and cena.janela.tela_pesquisa.linhas == []
    assert "Interação excluída" in cena.aviso


def test_excluir_pesquisa_pede_confirmacao_e_volta_para_a_lista(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa("Para apagar")
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    t = cena.janela.tela_pesquisa
    cena.responder(False)  # desiste
    cena.clicar(t.botao_excluir)
    assert cena.tela is t and "1 interação registrada" in cena.perguntas[-1][1]
    cena.responder(True)
    cena.clicar(t.botao_excluir)
    assert cena.tela is cena.janela.tela_pesquisas and cena.janela.tela_pesquisas.linhas == []
    assert "Pesquisa excluída" in cena.aviso


def test_pesquisa_concluida_nao_mostra_o_botao_de_excluir(cena):
    montar_pesquisa_com_tres_fontes(cena)
    t = cena.janela.tela_pesquisa
    assert t.botao_excluir.isVisible()
    cena.responder(True)
    cena.clicar(t.botao_concluir)
    cena.clicar(cena.janela.tela_relatorio.botao_voltar)
    assert not cena.janela.tela_pesquisa.botao_excluir.isVisible()


# ================================================================ fontes (RF15 a RF19, RF26, RF27)
def test_fonte_nova_aparece_nao_verificada_com_referencia_e_link(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    assert "Nenhuma fonte cadastrada" in cena.textos(cena.tela)
    cena.adicionar_fonte("Silva (2023)", "https://doi.org/10.1/x")
    cena.adicionar_fonte("Sem link")
    c1, c2 = cena.janela.tela_interacao.cartoes
    assert c1.property("status") == "nao_verificada" and "Não verificada" in c1.selo.text()
    assert "https://doi.org/10.1/x" in c1.link.text() and c1.link.openExternalLinks()
    assert not hasattr(c2, "link")
    assert "2 fontes • 2 pendentes" in cena.textos(cena.tela)


def test_fonte_sem_referencia_mostra_o_erro_no_formulario(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    vistos = []
    cena.dialogo({"referencia": "  ", "link": "x"}, depois=lambda d: vistos.append(d.erro.text()))
    cena.clicar(cena.janela.tela_interacao.botao_adicionar_fonte)
    assert vistos and "referência" in vistos[0] and cena.janela.tela_interacao.cartoes == []


def test_verificar_fonte_com_anotacao_e_trecho_aparece_ao_lado_da_fonte(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    cena.verificacao("verificada", "Confere com o livro", "A IA mudou o ensino.", "parágrafo 2")
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    c = cena.cartao("Silva (2023)")
    assert c.property("status") == "verificada" and "Verificada" in c.selo.text()
    assert "Anotação: Confere com o livro" in cena.textos(c)
    assert [t.text() for t in c.trechos] == ["“A IA mudou o ensino.”  (parágrafo 2)"]  # RF27
    assert "Verificação salva" in cena.aviso
    assert "verificada" in cena.textos(cena.tela)  # RF19: o resumo da interação


def test_ligar_outro_trecho_a_fonte_verificada(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    assert not cena.cartao("Silva (2023)").botao_trecho.isVisible()  # só depois de verificada
    cena.verificacao("verificada", trecho="primeiro")
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    cena.dialogo({"trecho": "segundo", "localizacao": "linha 10"})
    cena.clicar(cena.cartao("Silva (2023)").botao_trecho)
    textos = [t.text() for t in cena.cartao("Silva (2023)").trechos]
    assert textos == ["“primeiro”", "“segundo”  (linha 10)"]


def test_o_status_vai_e_volta_nos_tres_sentidos_e_avisa_dos_trechos(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    cena.verificacao("verificada", trecho="meu texto")
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    avisos = []
    cena.verificacao("incorreta", "O ano é outro", antes=lambda d: d.opcoes["incorreta"].setChecked(True) or avisos.append(d.aviso_trechos.isVisibleTo(d)))
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    assert avisos == [True]  # o diálogo avisou que o trecho será removido
    c = cena.cartao("Silva (2023)")
    assert c.property("status") == "incorreta" and c.trechos == []
    cena.verificacao("nao_verificada")
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    assert cena.cartao("Silva (2023)").property("status") == "nao_verificada"


def test_o_dialogo_de_verificacao_so_libera_o_trecho_para_fonte_verificada(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    estados = []

    def olhar(d):
        for chave in ("verificada", "incorreta", "nao_verificada"):
            d.opcoes[chave].setChecked(True)
            estados.append((chave, d.grupo_trecho.isEnabled()))

    cena.dialogo(clicar="cancelar", antes=olhar)
    # o diálogo de verificação não é um formulário comum: o roteiro acima só usa botao_cancelar
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    assert estados == [("verificada", True), ("incorreta", False), ("nao_verificada", False)]


def test_o_dialogo_troca_o_rotulo_da_anotacao_para_fonte_incorreta_e_cartao_mostra_sem_trecho(cena):
    """Protótipo, telas 5, 7 e 8: anotação de correção só se pede para 'incorreta'; sem trecho é dito."""
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    assert "Ainda sem trecho vinculado." in cena.textos(cena.cartao("Silva (2023)"))
    rotulos = []

    def olhar(d):
        for chave in ("incorreta", "verificada"):
            d.opcoes[chave].setChecked(True)
            rotulos.append(d.rotulo_anotacao.text())

    cena.dialogo(clicar="cancelar", antes=olhar)
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    assert "Anotação de correção" in rotulos[0] and "Anotação de correção" not in rotulos[1]

    cena.verificacao("incorreta", "Não existe")
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    assert "Fonte descartada" in cena.textos(cena.cartao("Silva (2023)"))
    cena.clicar(cena.janela.tela_interacao.botao_voltar)
    cena.clicar(cena.janela.tela_pesquisa.botao_relatorio)
    assert "sem trecho (fonte descartada)" in cena.janela.tela_relatorio.texto()


# ================================================================ concluir e relatório (RF10, RF20 a RF23, RF28)
def montar_pesquisa_com_tres_fontes(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa("Impacto da IA", "Entender o uso de IA")
    cena.registrar_interacao("ChatGPT", "Qual o efeito da IA?", "Grande <b>efeito</b>.")
    cena.adicionar_fonte("Silva (2023)", "https://doi.org/10.1/x")
    cena.adicionar_fonte("Inventada (2099)")
    cena.adicionar_fonte("Souza (2020)")
    cena.verificacao("verificada", "Confere", "A IA mudou o ensino.", "§2")
    cena.clicar(cena.cartao("Silva (2023)").botao_verificar)
    cena.verificacao("incorreta", "O DOI não existe")
    cena.clicar(cena.cartao("Inventada (2099)").botao_verificar)
    cena.clicar(cena.janela.tela_interacao.botao_voltar)


def test_aluno_ve_a_previa_do_relatorio_antes_de_concluir(cena):
    montar_pesquisa_com_tres_fontes(cena)
    cena.clicar(cena.janela.tela_pesquisa.botao_relatorio)
    r = cena.janela.tela_relatorio
    assert cena.tela is r
    texto = r.texto()
    assert "Prévia: a pesquisa ainda não foi concluída" in texto
    assert "Ao concluir a pesquisa" in cena.textos(r)
    # o texto do usuário aparece como foi digitado, sem virar HTML
    assert "Grande <b>efeito</b>." in texto
    cena.clicar(r.botao_voltar)
    assert cena.tela is cena.janela.tela_pesquisa


def test_concluir_avisa_das_fontes_pendentes_gera_o_relatorio_e_trava_a_pesquisa(cena):
    montar_pesquisa_com_tres_fontes(cena)
    t = cena.janela.tela_pesquisa
    cena.responder(False)
    cena.clicar(t.botao_concluir)  # o aluno desiste
    assert "1 fonte sem verificar" in cena.perguntas[-1][1]
    assert cena.tela is t and t.pesquisa.status == "em_andamento"

    cena.responder(True)
    cena.clicar(t.botao_concluir)
    r = cena.janela.tela_relatorio
    assert cena.tela is r
    texto = r.texto()
    assert "Entregue em" in texto and "Prévia" not in texto
    assert "Impacto da IA" in texto and "Ana" in texto
    assert "1 verificada" in texto and "1 incorreta" in texto and "1 não verificada" in texto
    assert "“A IA mudou o ensino.”" in texto and "(§2)" in texto  # RF28
    assert "Anotação do aluno: O DOI não existe" in texto  # RF18
    assert "disponível para o professor" in cena.aviso

    cena.clicar(r.botao_voltar)
    t = cena.janela.tela_pesquisa
    assert "Concluída" in t.selo.text()
    for escondido in (t.botao_editar, t.botao_concluir, t.botao_nova_interacao):
        assert not escondido.isVisible()
    assert t.botao_relatorio.isVisible() and t.botao_relatorio.text() == "Ver relatório"
    # e a interação e as fontes também não podem mais ser alteradas
    cena.clicar(t.linhas[0])
    i = cena.janela.tela_interacao
    assert not i.botao_editar.isVisible() and not i.botao_excluir.isVisible()
    assert not i.botao_adicionar_fonte.isVisible()
    assert all(not c.botao_verificar.isVisible() for c in i.cartoes)


def test_professor_so_ve_o_que_foi_entregue_e_abre_o_relatorio(cena):
    montar_pesquisa_com_tres_fontes(cena)
    cena.responder(True)
    cena.clicar(cena.janela.tela_pesquisa.botao_concluir)
    # Ana ainda cria outra pesquisa e não conclui
    cena.clicar(cena.janela.tela_relatorio.botao_voltar)
    cena.clicar(cena.janela.tela_pesquisa.botao_voltar)
    cena.criar_pesquisa("Rascunho", "Ainda escrevendo")
    cena.sair()

    cena.entrar_como_professor()
    p = cena.janela.tela_professor
    assert "Profa · Professor" in cena.janela.rotulo_usuario.text()
    assert len(p.linhas) == 1  # só a entregue
    linha = cena.textos(p.linhas[0])
    assert "Ana" in linha and "Impacto da IA" in linha and "Rascunho" not in cena.textos(p)
    assert "1/3 verificadas" in linha and "1 incorreta" in linha and "1 pendente" in linha
    cena.clicar(p.linhas[0])
    r = cena.janela.tela_relatorio
    assert cena.tela is r
    assert "Entregue em" in r.texto() and "“A IA mudou o ensino.”" in r.texto()
    assert "Isto é uma prévia" not in cena.textos(r)
    cena.clicar(r.botao_voltar)
    assert cena.tela is p


def test_professor_sem_entregas_ve_a_mensagem_de_lista_vazia(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.sair()
    cena.entrar_como_professor()
    assert "Nenhum relatório recebido ainda" in cena.textos(cena.tela)


def test_salvar_o_relatorio_em_pdf(cena):
    montar_pesquisa_com_tres_fontes(cena)
    cena.clicar(cena.janela.tela_pesquisa.botao_relatorio)
    cena.arquivo_pdf = str(cena.tmp / "relatorio")  # sem .pdf: a tela completa
    cena.clicar(cena.janela.tela_relatorio.botao_pdf)
    arquivo = cena.tmp / "relatorio.pdf"
    assert arquivo.exists() and arquivo.read_bytes().startswith(b"%PDF") and arquivo.stat().st_size > 2000
    assert "Relatório salvo" in cena.aviso
    # desistir de salvar não faz nada
    cena.arquivo_pdf = ""
    cena.clicar(cena.janela.tela_relatorio.botao_pdf)


def test_exportar_pdf_direto(tmp_path):
    destino = tmp_path / "a.pdf"
    exportar_pdf("<h1>Teste</h1><p>acentuação: ção</p>", str(destino))
    assert destino.read_bytes().startswith(b"%PDF")


# ================================================================ RF03: cada perfil no seu lugar
def test_aluno_nao_abre_a_area_do_professor(cena):
    cena.entrar_como_aluno()
    j = cena.janela
    assert j.mostrar(j.tela_professor) is False
    assert cena.tela is j.tela_pesquisas and "exclusiva de professores" in cena.aviso
    assert j.abrir_professor() is False
    assert cena.tela is j.tela_pesquisas


def test_professor_nao_abre_as_telas_do_aluno_nem_por_numero(cena):
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.sair()
    cena.entrar_como_professor()
    j = cena.janela
    for abrir in (j.abrir_pesquisas, lambda: j.abrir_pesquisa(1), lambda: j.abrir_interacao(1)):
        assert abrir() is False
        assert cena.tela is j.tela_professor and "exclusiva de alunos" in cena.aviso
    # o relatório de uma pesquisa em andamento também não abre para ele
    assert j.abrir_relatorio(1, "‹ Voltar", j.abrir_professor) is False
    assert cena.tela is j.tela_professor and "não encontrada" in cena.aviso


def test_sem_login_so_a_tela_de_acesso_abre(cena):
    j = cena.janela
    for abrir in (j.abrir_pesquisas, j.abrir_professor, lambda: j.abrir_pesquisa(1), lambda: j.abrir_interacao(1)):
        assert abrir() is False
        assert cena.tela is j.tela_acesso and "Entre na sua conta" in cena.aviso


def test_aluno_nao_abre_pesquisa_de_outro_aluno_pelo_numero(cena):
    cena.entrar_como_aluno("Ana", "ana@x.com")
    cena.criar_pesquisa("Da Ana", "O")
    cena.registrar_interacao()
    ids = (cena.janela.tela_pesquisa.pesquisa_id, cena.janela.tela_interacao.interacao_id)
    cena.sair()
    cena.entrar_como_aluno("Bia", "bia@x.com")
    j = cena.janela
    assert j.abrir_pesquisa(ids[0]) is False and "não encontrada" in cena.aviso
    assert j.abrir_interacao(ids[1]) is False and "não encontrada" in cena.aviso
    assert j.abrir_relatorio(ids[0], "‹", j.abrir_pesquisas) is False
    assert cena.tela is j.tela_pesquisas


# ================================================================ visual
def test_a_folha_de_estilo_nao_tem_erro_de_sintaxe(app):
    mensagens = []
    qInstallMessageHandler(lambda tipo, contexto, texto: mensagens.append(texto))
    try:
        from PySide6.QtWidgets import QWidget

        w = QWidget()
        w.setStyleSheet(estilo.folha_de_estilo())
        w.ensurePolished()
    finally:
        qInstallMessageHandler(None)
    assert not [m for m in mensagens if "stylesheet" in m.lower() or "parse" in m.lower()], mensagens


def test_a_janela_cabe_em_tela_pequena(cena):
    cena.janela.resize(860, 560)
    cena.entrar_como_aluno()
    cena.criar_pesquisa()
    cena.registrar_interacao()
    cena.adicionar_fonte("Silva (2023)")
    cena.app.processEvents()
    assert cena.janela.width() >= 860 and cena.tela.isVisible()
