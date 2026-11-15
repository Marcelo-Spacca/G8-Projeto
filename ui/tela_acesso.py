"""Tela de acesso: entrar (RF02) e criar conta (RF01)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ui.componentes import botao, linha_horizontal, mensagem_de_erro, rotulo


class _Paginas(QWidget):
    """Mostra uma página por vez. Diferente do QStackedWidget, a altura acompanha só a página
    visível, então a tela de entrar não fica esticada até a altura da de criar conta."""

    def __init__(self):
        super().__init__()
        self._v = QVBoxLayout(self)
        self._v.setContentsMargins(0, 0, 0, 0)
        self._paginas = []
        self._atual = 0

    def addWidget(self, pagina):
        self._paginas.append(pagina)
        self._v.addWidget(pagina)
        pagina.setVisible(len(self._paginas) == 1)

    def setCurrentIndex(self, indice):
        self._atual = indice
        for n, pagina in enumerate(self._paginas):
            pagina.setVisible(n == indice)

    def currentIndex(self):
        return self._atual


def _campo(layout, texto, dica="", senha=False):
    layout.addWidget(rotulo(texto, "campo", quebra=False))
    entrada = QLineEdit()
    entrada.setPlaceholderText(dica)
    if senha:
        entrada.setEchoMode(QLineEdit.Password)
    layout.addWidget(entrada)
    return entrada


class TelaAcesso(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 56, 24, 24)
        centro = QHBoxLayout()
        raiz.addLayout(centro)
        raiz.addStretch(1)

        cartao = QFrame()
        cartao.setProperty("papel", "painel")
        cartao.setFixedWidth(450)
        interno = QVBoxLayout(cartao)
        interno.setContentsMargins(32, 30, 32, 28)
        interno.setSpacing(8)
        self.paginas = _Paginas()
        interno.addWidget(self.paginas)
        centro.addStretch(1)
        centro.addWidget(cartao, 0, Qt.AlignTop)
        centro.addStretch(1)

        self._montar_login()
        self._montar_cadastro()

    # ------------------------------------------------------------ montagem
    def _montar_login(self):
        pagina = QWidget()
        v = QVBoxLayout(pagina)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addWidget(rotulo("Entrar", "titulo"))
        v.addWidget(rotulo("Registre o que a IA respondeu, confira cada fonte e entregue o relatório ao professor.", "mudo"))
        v.addSpacing(10)
        self.login_email = _campo(v, "E-mail", "voce@exemplo.com")
        self.login_senha = _campo(v, "Senha", senha=True)
        self.login_mensagem = rotulo("", "erro")
        self.login_mensagem.hide()
        v.addWidget(self.login_mensagem)
        v.addSpacing(6)
        self.botao_entrar = botao("Entrar", "primario", self.entrar)
        v.addWidget(self.botao_entrar)
        self.botao_ir_cadastro = botao("Ainda não tem conta? Criar conta", "link", self.ir_para_cadastro)
        v.addLayout(linha_horizontal(None, self.botao_ir_cadastro, None))
        self.login_email.returnPressed.connect(self.login_senha.setFocus)
        self.login_senha.returnPressed.connect(self.entrar)
        self.paginas.addWidget(pagina)

    def _montar_cadastro(self):
        pagina = QWidget()
        v = QVBoxLayout(pagina)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        v.addWidget(rotulo("Criar conta", "titulo"))
        v.addWidget(rotulo("Com a conta de aluno você registra o uso de IA; com a de professor, recebe os relatórios.", "mudo"))
        v.addSpacing(10)
        self.cad_nome = _campo(v, "Nome", "Como você quer ser chamado")
        self.cad_email = _campo(v, "E-mail", "voce@exemplo.com")
        self.cad_senha = _campo(v, "Senha", "Pelo menos 6 caracteres", senha=True)
        v.addWidget(rotulo("Você é", "campo", quebra=False))
        self.radio_aluno = QRadioButton("Aluno")
        self.radio_professor = QRadioButton("Professor")
        self.radio_aluno.setChecked(True)
        v.addLayout(linha_horizontal(self.radio_aluno, self.radio_professor, None, espaco=24))
        self.cad_mensagem = rotulo("", "erro")
        self.cad_mensagem.hide()
        v.addWidget(self.cad_mensagem)
        v.addSpacing(6)
        self.botao_criar_conta = botao("Criar conta", "primario", self.cadastrar)
        v.addWidget(self.botao_criar_conta)
        self.botao_ir_login = botao("Já tem conta? Entrar", "link", self.ir_para_login)
        v.addLayout(linha_horizontal(None, self.botao_ir_login, None))
        self.cad_senha.returnPressed.connect(self.cadastrar)
        self.paginas.addWidget(pagina)

    # ------------------------------------------------------------ ações
    def reiniciar(self):
        """Volta para a página de entrada, com os campos limpos (ao abrir o programa ou sair da conta)."""
        for campo in (self.login_email, self.login_senha, self.cad_nome, self.cad_email, self.cad_senha):
            campo.clear()
        self.radio_aluno.setChecked(True)
        self.login_mensagem.hide()
        self.cad_mensagem.hide()
        self.paginas.setCurrentIndex(0)
        self.login_email.setFocus()

    def _mostrar(self, rotulo_, texto, papel):
        rotulo_.setProperty("papel", papel)
        rotulo_.style().unpolish(rotulo_)
        rotulo_.style().polish(rotulo_)
        rotulo_.setText(texto)
        rotulo_.setVisible(bool(texto))

    def ir_para_cadastro(self):
        self.login_mensagem.hide()
        self.paginas.setCurrentIndex(1)
        self.cad_nome.setFocus()

    def ir_para_login(self, email=None, mensagem=None):
        self.cad_mensagem.hide()
        self.paginas.setCurrentIndex(0)
        if email:
            self.login_email.setText(email)
        if mensagem:
            self._mostrar(self.login_mensagem, mensagem, "ok")
        else:
            self.login_mensagem.hide()
        (self.login_senha if email else self.login_email).setFocus()

    def entrar(self):
        self.login_mensagem.hide()
        try:
            self.janela.usuarios.entrar(self.login_email.text(), self.login_senha.text())
        except Exception as erro:
            self._mostrar(self.login_mensagem, mensagem_de_erro(erro), "erro")
            return
        self.janela.entrou()

    def cadastrar(self):
        self.cad_mensagem.hide()
        tipo = "aluno" if self.radio_aluno.isChecked() else "professor"
        try:
            self.janela.usuarios.cadastrar(
                self.cad_nome.text(), self.cad_email.text(), self.cad_senha.text(), tipo
            )
        except Exception as erro:
            self._mostrar(self.cad_mensagem, mensagem_de_erro(erro), "erro")
            return
        email = self.cad_email.text().strip().lower()
        self.cad_nome.clear()
        self.cad_email.clear()
        self.cad_senha.clear()
        self.ir_para_login(email=email, mensagem="Conta criada. Digite sua senha para entrar.")
