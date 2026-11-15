"""Relatório de uma pesquisa (RF20, RF21, RF28). Serve ao aluno (prévia ou entregue) e ao professor."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPageSize, QPdfWriter, QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QTextBrowser, QVBoxLayout, QWidget

from ui import componentes as c
from ui import relatorio_html


def exportar_pdf(html, caminho):
    """Grava o HTML do relatório num arquivo PDF (A4)."""
    documento = QTextDocument()
    fonte = QFont()
    fonte.setFamilies(["Georgia", "Cambria", "Times New Roman", "DejaVu Serif", "serif"])
    fonte.setPointSizeF(10.5)
    documento.setDefaultFont(fonte)
    documento.setHtml(html)
    escritor = QPdfWriter(caminho)
    escritor.setPageSize(QPageSize(QPageSize.A4))
    documento.print_(escritor)


class TelaRelatorio(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.html = ""
        self.gerado = None
        externo = QHBoxLayout(self)
        externo.setContentsMargins(24, 28, 24, 24)
        coluna = QWidget()
        coluna.setMaximumWidth(c.LARGURA_COLUNA + 120)
        externo.addStretch(1)
        externo.addWidget(coluna, 100)
        externo.addStretch(1)
        self.v = QVBoxLayout(coluna)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.v.setSpacing(12)
        self.cabecalho = QVBoxLayout()
        self.v.addLayout(self.cabecalho)
        self.visor = QTextBrowser()
        self.visor.setOpenExternalLinks(True)
        self.visor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.v.addWidget(self.visor, 1)

    def carregar(self, pesquisa_id, texto_voltar, acao_voltar):
        gerado = self.janela.relatorios.gerar(pesquisa_id)
        self.gerado = gerado
        self.html = relatorio_html.montar(gerado)
        c.limpar(self.cabecalho)
        self.botao_voltar = c.botao(texto_voltar, "link", acao_voltar)
        self.botao_pdf = c.botao("Salvar como PDF", ao_clicar=self.salvar_pdf)
        self.cabecalho.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.titulo = c.rotulo("Relatório", "titulo", quebra=False)
        self.cabecalho.addLayout(c.linha_horizontal(self.titulo, None, self.botao_pdf))
        if gerado.entregue:
            quem = "O professor recebeu este relatório quando a pesquisa foi concluída."
        elif self.janela.perfil == "aluno":
            quem = "Isto é uma prévia. Ao concluir a pesquisa, o relatório é gerado e entregue ao professor."
        else:
            quem = ""
        self.nota = c.rotulo(quem, "mudo")
        self.nota.setVisible(bool(quem))
        self.cabecalho.addWidget(self.nota)
        self.visor.setHtml(self.html)
        self.visor.verticalScrollBar().setValue(0)

    def texto(self):
        """O relatório em texto puro (útil para conferir o que está na tela)."""
        return self.visor.toPlainText()

    def salvar_pdf(self):
        sugestao = f"relatorio-{c.cortar(self.gerado.pesquisa.titulo, 40).replace(' ', '-').lower()}.pdf"
        caminho = c.escolher_arquivo_pdf(self.janela, sugestao)
        if not caminho:
            return
        if not caminho.lower().endswith(".pdf"):
            caminho += ".pdf"
        try:
            exportar_pdf(self.html, caminho)
        except Exception as erro:
            self.janela.aviso(c.mensagem_de_erro(erro), "erro")
            return
        self.janela.aviso(f"Relatório salvo em {caminho}", "ok")
