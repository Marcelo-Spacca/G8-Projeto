"""Aparência do programa: cores, fontes e a folha de estilo (QSS) de todas as telas.

Ideia visual: o programa é um registro acadêmico. O que pertence ao documento (títulos de
pesquisa, trechos, relatório) usa fonte com serifa; os controles usam fonte sem serifa. A cor
fica contida (tinta azul-marinho sobre papel frio) para que a única informação colorida da tela
seja o status de cada fonte: verificada, incorreta ou ainda não verificada.
"""
from string import Template

# Fontes (a primeira que existir no computador é usada)
SERIFA = '"Georgia", "Cambria", "Times New Roman", "DejaVu Serif", serif'
SEM_SERIFA = '"Segoe UI", "Inter", "Helvetica Neue", "Arial", sans-serif'

# Cores
TINTA = "#14213D"        # barra superior e títulos
PAPEL = "#F5F7FA"        # fundo da janela
SUPERFICIE = "#FFFFFF"   # campos, listas, janelas de diálogo
LINHA = "#D8DEE8"        # fios e bordas
TEXTO = "#1C2430"
MUDO = "#5B6778"
PRIMARIO = "#24408E"
PRIMARIO_FORTE = "#1A3170"
REALCE = "#EEF2FA"       # linha sob o mouse

VERDE, VERDE_FUNDO = "#1B7547", "#E2F3E9"
VERMELHO, VERMELHO_FUNDO = "#B3372B", "#FBE8E5"
AMBAR, AMBAR_FUNDO = "#8A5600", "#FFF0CF"
AZUL, AZUL_FUNDO = PRIMARIO, "#E5ECFA"

# Cor e fundo de cada status (usados nas telas e no relatório)
CORES_STATUS = {
    "verificada": (VERDE, VERDE_FUNDO),
    "incorreta": (VERMELHO, VERMELHO_FUNDO),
    "pendente": (AMBAR, AMBAR_FUNDO),
    "andamento": (AZUL, AZUL_FUNDO),
}

_FOLHA = Template(
    """
QWidget {
    font-family: $SEM_SERIFA;
    font-size: 14px;
    color: $TEXTO;
}
QMainWindow, QWidget#fundo, QScrollArea, QScrollArea > QWidget > QWidget#conteudo {
    background: $PAPEL;
}
QScrollArea { border: none; }

/* barras de rolagem finas */
QScrollBar:vertical { background: transparent; width: 12px; margin: 2px; }
QScrollBar::handle:vertical { background: #C3CBD8; border-radius: 4px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #9AA9C9; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px; }
QScrollBar::handle:horizontal { background: #C3CBD8; border-radius: 4px; min-width: 36px; }
QScrollBar::handle:horizontal:hover { background: #9AA9C9; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* barra superior */
QFrame#barra { background: $TINTA; }
QFrame#barra QLabel { color: #FFFFFF; background: transparent; }
QLabel#marca { font-family: $SERIFA; font-size: 17px; font-weight: 600; }
QLabel#quem { color: #C9D3E6; font-size: 13px; }
QFrame#barra QPushButton {
    background: transparent; color: #FFFFFF; border: 1px solid #5B6B8C; padding: 5px 14px;
}
QFrame#barra QPushButton:hover { background: #22325A; }

/* avisos no topo da tela */
QLabel#aviso { padding: 10px 18px; font-size: 14px; }
QLabel#aviso[tipo="erro"] { background: $VERMELHO_FUNDO; color: $VERMELHO; border-bottom: 1px solid $VERMELHO; }
QLabel#aviso[tipo="ok"] { background: $VERDE_FUNDO; color: $VERDE; border-bottom: 1px solid $VERDE; }
QLabel#aviso[tipo="info"] { background: $AZUL_FUNDO; color: $AZUL; border-bottom: 1px solid $AZUL; }

/* textos */
QLabel[papel="titulo"] { font-family: $SERIFA; font-size: 28px; font-weight: 600; color: $TINTA; }
QLabel[papel="secao"] { font-family: $SERIFA; font-size: 19px; font-weight: 600; color: $TINTA; }
QLabel[papel="mudo"] { color: $MUDO; }
QLabel[papel="campo"] { font-weight: 600; font-size: 13px; }
QLabel[papel="dica"] { color: $MUDO; font-size: 12px; }
QLabel[papel="documento"] { font-family: $SERIFA; font-size: 15px; line-height: 150%; }
QLabel[papel="erro"] { color: $VERMELHO; font-size: 13px; }
QLabel[papel="ok"] { color: $VERDE; font-size: 13px; }
QLabel[papel="item"] { font-family: $SERIFA; font-size: 16px; font-weight: 600; color: $TINTA; }
QLabel[papel="vazio"] { color: $MUDO; font-family: $SERIFA; font-size: 15px; padding: 28px 8px; }

QLabel[papel="recado_titulo"] { font-weight: 700; font-size: 14px; background: transparent; }
QLabel[papel="recado_texto"] { font-family: $SERIFA; font-size: 15px; background: transparent; }

/* selos de status */
QLabel[chip] { padding: 3px 11px; border-radius: 10px; font-size: 12px; font-weight: 600; }
QLabel[chip="verificada"] { background: $VERDE_FUNDO; color: $VERDE; }
QLabel[chip="incorreta"] { background: $VERMELHO_FUNDO; color: $VERMELHO; }
QLabel[chip="pendente"] { background: $AMBAR_FUNDO; color: $AMBAR; }
QLabel[chip="andamento"] { background: $AZUL_FUNDO; color: $AZUL; }
QLabel[chip="neutro"] { background: #E9EDF3; color: $MUDO; }

/* botões */
QPushButton {
    background: $SUPERFICIE; border: 1px solid #B9C2D0; border-radius: 6px;
    padding: 8px 16px; font-weight: 600; color: $TINTA;
}
QPushButton:hover { background: $REALCE; }
QPushButton:focus { border: 2px solid $PRIMARIO; padding: 7px 15px; }
QPushButton:disabled { color: #9AA4B2; background: #F0F2F6; border-color: $LINHA; }
QPushButton[tipo="primario"] { background: $PRIMARIO; color: #FFFFFF; border: 1px solid $PRIMARIO; }
QPushButton[tipo="primario"]:hover { background: $PRIMARIO_FORTE; }
QPushButton[tipo="primario"]:disabled { background: #AAB6D3; border-color: #AAB6D3; color: #FFFFFF; }
QPushButton[tipo="perigo"] { color: $VERMELHO; border: 1px solid #E3B4AE; }
QPushButton[tipo="perigo"]:hover { background: $VERMELHO_FUNDO; }
QPushButton[tipo="ajuda"] {
    background: $SUPERFICIE; color: $PRIMARIO; border: 1px solid #B9C2D0; border-radius: 13px;
    padding: 4px 12px; font-size: 12px; font-weight: 600; min-height: 18px;
}
QPushButton[tipo="ajuda"]:hover { background: $REALCE; border-color: $PRIMARIO; }
QPushButton[tipo="ajuda"]:focus { border: 2px solid $PRIMARIO; padding: 3px 11px; }
QPushButton[tipo="aba"] {
    background: transparent; border: none; border-bottom: 3px solid transparent; border-radius: 0;
    padding: 8px 18px; color: $MUDO; font-size: 15px;
}
QPushButton[tipo="aba"]:hover { background: transparent; color: $TINTA; }
QPushButton[tipo="aba"][ativa="sim"] { color: $TINTA; border-bottom: 3px solid $PRIMARIO; }
QPushButton[tipo="aba"]:focus { border: none; border-bottom: 3px solid $PRIMARIO; padding: 8px 18px; }
QPushButton[tipo="aba"]:disabled { color: #B3BBC8; background: transparent; border-bottom: 3px solid transparent; }
QPushButton[tipo="link"] {
    background: transparent; border: none; color: $PRIMARIO; padding: 4px 2px; font-weight: 600;
}
QPushButton[tipo="link"]:hover { text-decoration: underline; background: transparent; }

/* campos */
QLineEdit, QPlainTextEdit, QTextEdit {
    background: $SUPERFICIE; border: 1px solid #B9C2D0; border-radius: 6px; padding: 8px 10px;
    selection-background-color: $PRIMARIO; selection-color: #FFFFFF;
}
QLineEdit:focus, QPlainTextEdit:focus { border: 2px solid $PRIMARIO; padding: 7px 9px; }
QComboBox {
    background: $SUPERFICIE; color: $TEXTO; border: 1px solid #B9C2D0; border-radius: 6px;
    padding: 6px 12px; min-height: 22px; min-width: 200px;
}
QComboBox:hover { background: $REALCE; }
QComboBox:focus { border: 2px solid $PRIMARIO; padding: 5px 11px; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView, QComboBoxPrivateContainer {
    background: $SUPERFICIE; color: $TEXTO; border: 1px solid #B9C2D0; outline: 0; padding: 4px;
    selection-background-color: $REALCE; selection-color: $TINTA;
}
QComboBox QAbstractItemView::item { min-height: 30px; padding: 2px 10px; color: $TEXTO; background: $SUPERFICIE; }
QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected { background: $REALCE; color: $TINTA; }
QRadioButton, QCheckBox { spacing: 8px; padding: 4px 0; }
QLabel[papel="codigo"] {
    font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 15px; font-weight: 700;
    color: $TINTA; background: #E9EDF3; border: 1px dashed #9AA9C9; border-radius: 6px; padding: 3px 12px;
}
QTextBrowser { background: $SUPERFICIE; border: 1px solid $LINHA; border-radius: 8px; padding: 14px; font-family: $SERIFA; font-size: 14px; }

/* listas: linhas separadas por fio, sem um cartão para cada item */
QFrame[papel="lista"] { background: $SUPERFICIE; border: 1px solid $LINHA; border-radius: 8px; }
QFrame[papel="linha"] { background: transparent; border: none; border-bottom: 1px solid $LINHA; }
QFrame[papel="linha"][ultima="sim"] { border-bottom: none; }
QFrame[papel="linha"][clicavel="sim"]:hover { background: $REALCE; }
QFrame[papel="linha"][clicavel="sim"]:focus { background: $REALCE; }

/* fonte: a barra lateral colorida é o status */
QFrame[papel="fonte"] {
    background: $SUPERFICIE; border: 1px solid $LINHA; border-left: 6px solid #B9C2D0; border-radius: 6px;
}
QFrame[papel="fonte"][status="verificada"] { border-left: 6px solid $VERDE; }
QFrame[papel="fonte"][status="incorreta"] { border-left: 6px solid $VERMELHO; }
QFrame[papel="fonte"][status="nao_verificada"] { border-left: 6px solid #E0A526; }
QLabel[papel="trecho"] {
    font-family: $SERIFA; font-style: italic; font-size: 14px; color: $TEXTO;
    background: #F3F5F9; border-left: 3px solid #9AA9C9; padding: 6px 10px;
}

/* recados: devolução do professor, comentários e avisos de estado */
QFrame[papel="recado"] { border-radius: 8px; border: 1px solid $LINHA; background: #FFFFFF; }
QFrame[papel="recado"][tipo="devolucao"] { background: $VERMELHO_FUNDO; border: 1px solid #E3B4AE; border-left: 6px solid $VERMELHO; }
QFrame[papel="recado"][tipo="devolucao"] QLabel[papel="recado_titulo"] { color: $VERMELHO; }
QFrame[papel="recado"][tipo="comentario"] { background: $AZUL_FUNDO; border: 1px solid #C5D2EE; border-left: 6px solid $PRIMARIO; }
QFrame[papel="recado"][tipo="comentario"] QLabel[papel="recado_titulo"] { color: $PRIMARIO; }
QFrame[papel="recado"][tipo="aviso"] { background: $AMBAR_FUNDO; border: 1px solid #EBCB85; border-left: 6px solid #E0A526; }
QFrame[papel="recado"][tipo="aviso"] QLabel[papel="recado_titulo"] { color: $AMBAR; }
QFrame[papel="recado"][tipo="ok"] { background: $VERDE_FUNDO; border: 1px solid #A8D5BB; border-left: 6px solid $VERDE; }
QFrame[papel="recado"][tipo="ok"] QLabel[papel="recado_titulo"] { color: $VERDE; }

/* painéis de texto (pergunta e resposta) */
QFrame[papel="painel"] { background: $SUPERFICIE; border: 1px solid $LINHA; border-radius: 8px; }

/* janelas de diálogo */
QDialog { background: $SUPERFICIE; }
QDialog QScrollArea, QDialog QScrollArea > QWidget > QWidget { background: $SUPERFICIE; }
QMessageBox { background: $SUPERFICIE; }
QMessageBox QLabel { color: $TEXTO; }
QToolTip { background: $TINTA; color: #FFFFFF; border: none; padding: 4px 8px; }
"""
)


def folha_de_estilo():
    """Devolve a folha de estilo com as cores e fontes já preenchidas."""
    valores = {k: v for k, v in globals().items() if k.isupper() and isinstance(v, str)}
    return _FOLHA.substitute(valores)


def paleta_clara():
    """Paleta completa nas cores do programa. Em vez de partir da paleta do sistema (que no modo escuro
    é escura), todas as cores que o Qt usa para campos, listas, botões e textos são definidas aqui."""
    from PySide6.QtGui import QColor, QPalette

    c = QColor
    paleta = QPalette()
    cores = {
        QPalette.Window: PAPEL, QPalette.WindowText: TEXTO,
        QPalette.Base: SUPERFICIE, QPalette.AlternateBase: PAPEL,
        QPalette.Text: TEXTO, QPalette.Button: SUPERFICIE, QPalette.ButtonText: TEXTO,
        QPalette.ToolTipBase: SUPERFICIE, QPalette.ToolTipText: TEXTO,
        QPalette.PlaceholderText: MUDO, QPalette.BrightText: "#FFFFFF",
        QPalette.Highlight: PRIMARIO, QPalette.HighlightedText: "#FFFFFF",
        QPalette.Link: PRIMARIO, QPalette.LinkVisited: PRIMARIO,
    }
    for papel, cor in cores.items():
        paleta.setColor(papel, c(cor))
    for papel in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        paleta.setColor(QPalette.Disabled, papel, c(MUDO))
    return paleta


def aplicar(app):
    """Aplica o estilo a todo o programa."""
    from PySide6.QtGui import QColor, QPalette

    # Sempre o tema claro: no modo escuro do Windows, listas suspensas e caixas de diálogo nativas
    # ficavam escuras e ilegíveis em cima desta folha de estilo clara.
    try:
        from PySide6.QtCore import Qt

        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except Exception:  # versões do Qt sem essa chamada
        pass
    app.setPalette(paleta_clara())
    app.setStyleSheet(folha_de_estilo())
