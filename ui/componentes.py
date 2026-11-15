"""Peças reutilizáveis das telas: textos, selos de status, botões, listas e perguntas ao usuário.

Aqui não há regra de negócio nem acesso ao banco: só widgets.
"""
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.erros import RegraViolada

# Texto e cor do selo de cada status. A chave é o valor guardado no banco.
STATUS_PESQUISA = {
    "em_andamento": ("Em andamento", "andamento"),
    "concluida": ("Concluída", "verificada"),
}
STATUS_FONTE = {
    "verificada": ("✓ Verificada", "verificada"),
    "incorreta": ("✕ Incorreta ou inventada", "incorreta"),
    "nao_verificada": ("○ Não verificada", "pendente"),
}
LARGURA_COLUNA = 920

# Erros que não são regra de negócio (banco fora do ar, bug). Fica registrado aqui para os
# testes poderem conferir que nenhuma tela escondeu um erro inesperado.
ERROS_INESPERADOS = []


def mensagem_de_erro(erro):
    """Texto para o usuário. RegraViolada já vem escrita para ele; o resto vira um aviso técnico."""
    if isinstance(erro, RegraViolada):
        return str(erro)
    ERROS_INESPERADOS.append(erro)
    primeira_linha = (str(erro).strip().splitlines() or [""])[0][:160]
    return (
        f"Erro inesperado ({type(erro).__name__}: {primeira_linha}). "
        "Se for de conexão, confira se o PostgreSQL está rodando e o arquivo .env."
    )


# ---------------------------------------------------------------- textos e selos
def rotulo(texto="", papel=None, quebra=True, selecionavel=False):
    r = QLabel(texto)
    if papel:
        r.setProperty("papel", papel)
    r.setWordWrap(quebra)
    if quebra:  # ocupa a largura que sobrar em vez de se espremer ao lado dos botões
        r.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    if selecionavel:
        r.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return r


def selo(texto, tipo):
    """Etiqueta colorida pequena. tipo: verificada, incorreta, pendente, andamento ou neutro."""
    r = QLabel(texto)
    r.setProperty("chip", tipo)
    r.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    return r


def selo_status_fonte(status):
    texto, tipo = STATUS_FONTE[status]
    return selo(texto, tipo)


def selo_status_pesquisa(status):
    texto, tipo = STATUS_PESQUISA[status]
    return selo(texto, tipo)


def botao(texto, tipo="secundario", ao_clicar=None):
    """tipo: primario, secundario, perigo ou link."""
    b = QPushButton(texto)
    b.setProperty("tipo", tipo)
    b.setCursor(Qt.PointingHandCursor)
    if ao_clicar is not None:
        b.clicked.connect(lambda _marcado=False: ao_clicar())
    return b


def cortar(texto, limite):
    texto = " ".join((texto or "").split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def formatar_data(data):
    return data.strftime("%d/%m/%Y %H:%M") if data else "—"


def formatar_dia(data):
    return data.strftime("%d/%m/%Y") if data else "—"


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"


def resumo_fontes(contagem):
    """'3 fontes • 1 pendente' a partir da contagem por status de services.fonte_service."""
    total = sum(contagem.values())
    if total == 0:
        return "Nenhuma fonte"
    partes = [plural(total, "fonte", "fontes")]
    if contagem["nao_verificada"]:
        partes.append(plural(contagem["nao_verificada"], "pendente", "pendentes"))
    if contagem["incorreta"]:
        partes.append(plural(contagem["incorreta"], "incorreta", "incorretas"))
    if not contagem["nao_verificada"] and not contagem["incorreta"]:
        partes.append("todas verificadas" if total > 1 else "verificada")
    return " • ".join(partes)


# ---------------------------------------------------------------- listas
class Linha(QFrame):
    """Uma linha de lista. Se for clicável, avisa com o sinal 'clicado' (mouse ou Enter)."""

    clicado = Signal()

    def __init__(self, clicavel=False):
        super().__init__()
        self.setProperty("papel", "linha")
        self._clicavel = clicavel
        if clicavel:
            self.setProperty("clicavel", "sim")
            self.setCursor(Qt.PointingHandCursor)
            self.setFocusPolicy(Qt.StrongFocus)

    def mouseReleaseEvent(self, evento):
        dentro = QRect(0, 0, self.width(), self.height()).contains(evento.position().toPoint())
        if self._clicavel and evento.button() == Qt.LeftButton and dentro:
            self.clicado.emit()
        super().mouseReleaseEvent(evento)

    def keyPressEvent(self, evento):
        if self._clicavel and evento.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicado.emit()
        else:
            super().keyPressEvent(evento)


class Lista(QFrame):
    """Moldura com linhas separadas por fio. Use 'adicionar' e depois 'fechar'."""

    def __init__(self):
        super().__init__()
        self.setProperty("papel", "lista")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.linhas = []

    def adicionar(self, linha):
        self.linhas.append(linha)
        self._layout.addWidget(linha)
        return linha

    def fechar(self):
        """Tira o fio da última linha."""
        if self.linhas:
            self.linhas[-1].setProperty("ultima", "sim")


def limpar(layout):
    """Remove (e destrói) tudo o que está dentro de um layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            limpar(item.layout())


def linha_horizontal(*itens, espaco=10, margens=(0, 0, 0, 0)):
    """Layout horizontal com os itens dados. Use None para uma mola."""
    layout = QHBoxLayout()
    layout.setContentsMargins(*margens)
    layout.setSpacing(espaco)
    for item in itens:
        if item is None:
            layout.addStretch(1)
        else:
            # texto que quebra linha ocupa o espaço livre; sem isso ele se espreme ao lado dos botões
            layout.addWidget(item, 1 if isinstance(item, QLabel) and item.wordWrap() else 0)
    return layout


class TelaBase(QWidget):
    """Base das telas: rola quando a janela é pequena e mantém o conteúdo numa coluna legível."""

    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.NoFrame)
        externo.addWidget(rolagem)

        conteudo = QWidget()
        conteudo.setObjectName("conteudo")
        rolagem.setWidget(conteudo)
        laterais = QHBoxLayout(conteudo)
        laterais.setContentsMargins(24, 28, 24, 36)
        coluna = QWidget()
        coluna.setMaximumWidth(LARGURA_COLUNA)
        coluna.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        laterais.addStretch(1)
        laterais.addWidget(coluna, 100)
        laterais.addStretch(1)
        self.corpo = QVBoxLayout(coluna)
        self.corpo.setContentsMargins(0, 0, 0, 0)
        self.corpo.setSpacing(14)

    def reiniciar(self):
        """Esvazia a tela antes de montar de novo."""
        limpar(self.corpo)

    def vazio(self, texto):
        return rotulo(texto, "vazio")


# ---------------------------------------------------------------- perguntas ao usuário
def perguntar(parent, titulo, texto, rotulo_ok="Confirmar", perigo=False):
    """Pergunta sim/não. Devolve True se o usuário confirmar. (Os testes trocam esta função.)"""
    caixa = QMessageBox(parent)
    caixa.setWindowTitle(titulo)
    caixa.setIcon(QMessageBox.Warning if perigo else QMessageBox.Question)
    caixa.setText(titulo)
    caixa.setInformativeText(texto)
    ok = caixa.addButton(rotulo_ok, QMessageBox.AcceptRole)
    ok.setProperty("tipo", "perigo" if perigo else "primario")
    cancelar = caixa.addButton("Cancelar", QMessageBox.RejectRole)
    caixa.setDefaultButton(cancelar)
    caixa.exec()
    return caixa.clickedButton() is ok


def abrir(dialogo):
    """Mostra uma janela de diálogo e espera. (Os testes trocam esta função.)"""
    return dialogo.exec()


def escolher_arquivo_pdf(parent, nome_sugerido):
    """Pergunta onde salvar o PDF. Devolve o caminho ou '' se o usuário desistir."""
    caminho, _ = QFileDialog.getSaveFileName(parent, "Salvar relatório", nome_sugerido, "PDF (*.pdf)")
    return caminho
