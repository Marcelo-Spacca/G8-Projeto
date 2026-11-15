"""Minhas pesquisas: lista (RF07) e criação de pesquisa (RF06)."""
from PySide6.QtWidgets import QDialog, QVBoxLayout

from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario


class TelaPesquisas(c.TelaBase):
    def carregar(self):
        pesquisas = self.janela.pesquisas.listar_minhas()
        self.reiniciar()
        self.botao_nova = c.botao("+ Nova pesquisa", "primario", self.nova_pesquisa)
        self.corpo.addLayout(c.linha_horizontal(c.rotulo("Minhas pesquisas", "titulo", quebra=False), None, self.botao_nova))
        self.corpo.addWidget(c.rotulo("Cada pesquisa reúne as interações com IA de um trabalho.", "mudo"))
        self.linhas = []
        if not pesquisas:
            self.corpo.addWidget(self.vazio("Você ainda não criou nenhuma pesquisa. Crie a primeira para começar a registrar o uso de IA do seu trabalho."))
        else:
            lista = c.Lista()
            for p in pesquisas:
                self.linhas.append(lista.adicionar(self._linha(p)))
            lista.fechar()
            self.corpo.addWidget(lista)
        self.corpo.addStretch(1)

    def _linha(self, pesquisa):
        linha = c.Linha(clicavel=True)
        linha.pesquisa_id = pesquisa.id
        esquerda = QVBoxLayout()
        esquerda.setSpacing(3)
        esquerda.addWidget(c.rotulo(pesquisa.titulo, "item", quebra=False))
        esquerda.addWidget(c.rotulo(c.cortar(pesquisa.objetivo, 120), "mudo"))
        direita = QVBoxLayout()
        direita.setSpacing(4)
        direita.addWidget(c.selo_status_pesquisa(pesquisa.status))
        direita.addWidget(c.rotulo(f"Criada em {c.formatar_dia(pesquisa.data_criacao)}", "dica", quebra=False))
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(direita)
        linha.setLayout(conteudo)
        linha.clicado.connect(lambda pid=pesquisa.id: self.janela.abrir_pesquisa(pid))
        return linha

    def nova_pesquisa(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Nova pesquisa",
            [
                Campo("titulo", "Título", dica="Ex.: Impactos da IA na educação"),
                Campo("objetivo", "Objetivo: o que você quer descobrir?", "texto", altura=100),
            ],
            self._criar,
            rotulo_ok="Criar pesquisa",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_pesquisa(self._criada.id)
            self.janela.aviso("Pesquisa criada. Registre a primeira interação com a IA.", "ok")

    def _criar(self, valores):
        self._criada = self.janela.pesquisas.criar(valores["titulo"], valores["objetivo"])
