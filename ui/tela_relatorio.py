"""Relatório de uma pesquisa (RF20, RF21, RF28). Serve ao aluno (prévia ou entregue) e ao professor."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPageSize, QPdfWriter, QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QTextBrowser, QVBoxLayout, QWidget

from ui import componentes as c
from ui import relatorio_html
from ui.dialogos import DialogoTutorial


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
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.cabecalho.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.titulo = c.rotulo("Relatório", "titulo", quebra=False)
        self.cabecalho.addLayout(c.linha_horizontal(self.titulo, None, self.botao_tutorial, self.botao_pdf))
        if gerado.concluida:
            quem = "Pesquisa concluída: o professor aceitou este relatório."
        elif gerado.entregue and self.janela.perfil == "professor":
            quem = "O aluno entregou esta pesquisa para a sua verificação."
        elif gerado.entregue:
            quem = "Este relatório foi entregue ao professor, que está revisando."
        elif self.janela.perfil == "aluno":
            quem = "Isto é uma prévia. Ao entregar a pesquisa, o relatório fica disponível para o professor."
        else:
            quem = ""
        self.nota = c.rotulo(quem, "mudo")
        self.nota.setVisible(bool(quem))
        self.cabecalho.addWidget(self.nota)
        self.visor.setHtml(self.html)
        self.visor.verticalScrollBar().setValue(0)

    def tutorial(self):
        chave = "relatorio_professor" if self.janela.perfil == "professor" else "relatorio_aluno"
        c.abrir(DialogoTutorial(self.janela, chave))

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
