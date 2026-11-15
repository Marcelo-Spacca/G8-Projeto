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
QRadioButton { spacing: 8px; padding: 4px 0; }
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

/* painéis de texto (pergunta e resposta) */
QFrame[papel="painel"] { background: $SUPERFICIE; border: 1px solid $LINHA; border-radius: 8px; }

/* janelas de diálogo */
QDialog { background: $SUPERFICIE; }
QMessageBox { background: $SUPERFICIE; }
QMessageBox QLabel { color: $TEXTO; }
QToolTip { background: $TINTA; color: #FFFFFF; border: none; padding: 4px 8px; }
"""
)


def folha_de_estilo():
    """Devolve a folha de estilo com as cores e fontes já preenchidas."""
    valores = {k: v for k, v in globals().items() if k.isupper() and isinstance(v, str)}
    return _FOLHA.substitute(valores)


def aplicar(app):
    """Aplica o estilo a todo o programa."""
    from PySide6.QtGui import QColor, QPalette

    paleta = app.palette()
    paleta.setColor(QPalette.Link, QColor(PRIMARIO))  # links com a cor do programa, não o azul do sistema
    paleta.setColor(QPalette.LinkVisited, QColor(PRIMARIO))
    app.setPalette(paleta)
    app.setStyleSheet(folha_de_estilo())
