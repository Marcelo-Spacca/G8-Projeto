"""Janelas de diálogo: formulário genérico e a janela de verificação de fonte.

Cada diálogo recebe uma 'acao' (função) que chama o service. Se o service recusar
(RegraViolada), a mensagem aparece dentro do diálogo e ele continua aberto para o usuário corrigir.
"""
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QLineEdit,
    QPlainTextEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ui.componentes import botao, linha_horizontal, mensagem_de_erro, rotulo


@dataclass
class Campo:
    chave: str
    rotulo: str
    tipo: str = "linha"  # linha, texto (várias linhas) ou senha
    dica: str = ""
    altura: int = 110


class _DialogoBase(QDialog):
    def __init__(self, parent, titulo, subtitulo=None, largura=540):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(largura)
        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(28, 24, 28, 22)
        self.raiz.setSpacing(8)
        self.raiz.addWidget(rotulo(titulo, "secao"))
        if subtitulo:
            self.raiz.addWidget(rotulo(subtitulo, "mudo"))
        self.raiz.addSpacing(4)

    def _rodape(self, rotulo_ok):
        self.erro = rotulo("", "erro")
        self.erro.hide()
        self.raiz.addWidget(self.erro)
        self.botao_cancelar = botao("Cancelar", ao_clicar=self.reject)
        self.botao_cancelar.setAutoDefault(False)
        self.botao_ok = botao(rotulo_ok, "primario", self.confirmar)
        self.botao_ok.setDefault(True)
        self.raiz.addSpacing(6)
        self.raiz.addLayout(linha_horizontal(None, self.botao_cancelar, self.botao_ok))

    def mostrar_erro(self, texto):
        self.erro.setText(texto)
        self.erro.show()

    def confirmar(self):
        """Chama a ação; se der certo fecha o diálogo, senão mostra o motivo e continua aberto."""
        self.erro.hide()
        try:
            self.acao(self.valores())
        except Exception as erro:  # RegraViolada ou erro inesperado: ambos viram texto na janela
            self.mostrar_erro(mensagem_de_erro(erro))
            return
        self.accept()


class DialogoFormulario(_DialogoBase):
    def __init__(self, parent, titulo, campos, acao, rotulo_ok="Salvar", subtitulo=None, valores=None):
        super().__init__(parent, titulo, subtitulo)
        self.acao = acao
        self.campos = {}
        for campo in campos:
            self.raiz.addWidget(rotulo(campo.rotulo, "campo"))
            if campo.tipo == "texto":
                entrada = QPlainTextEdit()
                entrada.setFixedHeight(campo.altura)
                entrada.setTabChangesFocus(True)
            else:
                entrada = QLineEdit()
                if campo.tipo == "senha":
                    entrada.setEchoMode(QLineEdit.Password)
                entrada.returnPressed.connect(self.confirmar)
            entrada.setPlaceholderText(campo.dica)
            self.campos[campo.chave] = entrada
            self.raiz.addWidget(entrada)
        self._rodape(rotulo_ok)
        if valores:
            self.definir(**valores)
        if self.campos:
            next(iter(self.campos.values())).setFocus()

    def definir(self, **valores):
        for chave, texto in valores.items():
            entrada = self.campos[chave]
            if isinstance(entrada, QPlainTextEdit):
                entrada.setPlainText(texto or "")
            else:
                entrada.setText(texto or "")

    def valores(self):
        return {
            chave: (e.toPlainText() if isinstance(e, QPlainTextEdit) else e.text())
            for chave, e in self.campos.items()
        }


class DialogoVerificacao(_DialogoBase):
    """RF17/RF18/RF26: o aluno confere a fonte, anota o que encontrou e liga o trecho do texto."""

    OPCOES = (
        ("verificada", "Verificada: existe e confirma o que a IA disse"),
        ("incorreta", "Incorreta ou inventada"),
        ("nao_verificada", "Ainda não verificada"),
    )

    def __init__(self, parent, fonte, acao):
        super().__init__(parent, "Verificar fonte", "Confira a fonte por conta própria, fora da IA.", largura=600)
        self.acao = acao
        self.raiz.addWidget(rotulo(fonte.referencia, "item", selecionavel=True))
        if fonte.link:
            self.raiz.addWidget(rotulo(fonte.link, "mudo", selecionavel=True))
        self.raiz.addSpacing(6)
        self.raiz.addWidget(rotulo("Qual é o resultado da sua conferência?", "campo"))

        self.opcoes = {}
        grupo = QButtonGroup(self)
        for chave, texto in self.OPCOES:
            radio = QRadioButton(texto)
            grupo.addButton(radio)
            self.opcoes[chave] = radio
            self.raiz.addWidget(radio)
        self.raiz.addSpacing(4)
        self.rotulo_anotacao = rotulo("O que você encontrou (opcional)", "campo")
        self.raiz.addWidget(self.rotulo_anotacao)
        self.anotacao = QPlainTextEdit()
        self.anotacao.setFixedHeight(80)
        self.anotacao.setTabChangesFocus(True)
        self.anotacao.setPlaceholderText("Ex.: o artigo existe, mas o ano é 2021 e não 2023.")
        self.anotacao.setPlainText(fonte.anotacao_correcao or "")
        self.raiz.addWidget(self.anotacao)

        self.grupo_trecho = QWidget()
        interno = QVBoxLayout(self.grupo_trecho)
        interno.setContentsMargins(0, 0, 0, 0)
        interno.setSpacing(8)
        ja_ligados = len(fonte.trechos)
        titulo_trecho = "Em que trecho do seu texto você usou esta fonte? (opcional)"
        if ja_ligados:
            titulo_trecho = f"Ligar outro trecho do seu texto (opcional). Já há {ja_ligados} ligado(s)."
        interno.addWidget(rotulo(titulo_trecho, "campo"))
        self.trecho = QPlainTextEdit()
        self.trecho.setFixedHeight(80)
        self.trecho.setTabChangesFocus(True)
        self.trecho.setPlaceholderText("Cole aqui a frase ou o parágrafo do seu trabalho.")
        interno.addWidget(self.trecho)
        self.localizacao = QLineEdit()
        self.localizacao.setPlaceholderText("Onde fica: parágrafo ou linha (opcional)")
        interno.addWidget(self.localizacao)
        self.raiz.addWidget(self.grupo_trecho)

        self.aviso_trechos = rotulo(
            f"Os {ja_ligados} trechos ligados a esta fonte serão removidos."
            if ja_ligados != 1
            else "O trecho ligado a esta fonte será removido.",
            "erro",
        )
        self.aviso_trechos.hide()
        self._ja_ligados = ja_ligados
        self.raiz.addWidget(self.aviso_trechos)

        self._rodape("Salvar verificação")
        # só agora, com todos os campos criados, as opções passam a reagir à troca de status
        self.opcoes[fonte.status].setChecked(True)
        for radio in self.opcoes.values():
            radio.toggled.connect(self._atualizar)
        self._atualizar()

    def resultado(self):
        return next(chave for chave, radio in self.opcoes.items() if radio.isChecked())

    def _atualizar(self, *_):
        verificada = self.resultado() == "verificada"
        self.grupo_trecho.setEnabled(verificada)
        self.rotulo_anotacao.setText(
            "Anotação de correção: o que está errado nesta fonte? (opcional)"
            if self.resultado() == "incorreta"
            else "O que você encontrou (opcional)"
        )
        self.aviso_trechos.setVisible(not verificada and self._ja_ligados > 0)

    def valores(self):
        return {
            "resultado": self.resultado(),
            "anotacao": self.anotacao.toPlainText(),
            "trecho": self.trecho.toPlainText() if self.resultado() == "verificada" else "",
            "localizacao": self.localizacao.text(),
        }
