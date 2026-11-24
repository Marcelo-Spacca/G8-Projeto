"""Cartão que mostra uma fonte: referência, link, status, anotação e trechos ligados.

Usado pela tela do aluno e pela do professor; cada uma acrescenta os próprios botões."""
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ui import componentes as c


def montar(fonte, visao="aluno"):
    """Devolve o cartão da fonte (um QFrame com 'v', o layout vertical, para pôr botões)."""
    cartao = QFrame()
    cartao.setProperty("papel", "fonte")
    cartao.setProperty("status", fonte.status)
    cartao.fonte_id = fonte.id
    v = QVBoxLayout(cartao)
    v.setContentsMargins(18, 14, 18, 14)
    v.setSpacing(6)
    cartao.v = v
    selo = c.selo_status_fonte(fonte.status)
    referencia = c.rotulo(fonte.referencia, "item", selecionavel=True)
    selos = [selo]
    if fonte.julgada_pelo_professor:
        julgada = c.selo("Julgada pelo professor", "andamento")
        selos.append(julgada)
        cartao.selo_professor = julgada
    v.addLayout(c.linha_horizontal(referencia, *selos, espaco=8))
    cartao.selo = selo
    cartao.referencia = referencia
    if fonte.link:
        link = QLabel()
        link.setWordWrap(True)
        if fonte.link.lower().startswith(("http://", "https://")):
            link.setText(f'<a href="{escape(fonte.link, quote=True)}">{escape(fonte.link)}</a>')
            link.setOpenExternalLinks(True)
        else:
            link.setText(fonte.link)
            link.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(link)
        cartao.link = link
    if fonte.anotacao_correcao:
        quem = "professor" if fonte.julgada_pelo_professor else ("aluno" if visao == "professor" else None)
        prefixo = f"Anotação do {quem}" if quem else "Anotação"
        cartao.anotacao = c.rotulo(f"{prefixo}: {fonte.anotacao_correcao}", "mudo", selecionavel=True)
        v.addWidget(cartao.anotacao)
    cartao.trechos = []
    trechos = sorted(fonte.trechos, key=lambda t: t.id)
    texto_dele = "no texto do aluno" if visao == "professor" else "no seu texto"
    if trechos:
        v.addWidget(c.rotulo(f"Usada {texto_dele} em:", "dica"))
    else:
        if fonte.status == "incorreta":
            sem = f"Fonte descartada: sem trecho {texto_dele}."
        else:
            sem = "Ainda sem trecho vinculado."
        v.addWidget(c.rotulo(sem, "dica"))
    for t in trechos:
        onde = f"  ({t.localizacao})" if t.localizacao else ""
        texto = c.rotulo(f"“{t.trecho_citado}”{onde}", "trecho", selecionavel=True)
        cartao.trechos.append(texto)
        v.addWidget(texto)
    return cartao
