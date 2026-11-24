"""Minhas turmas (aluno): as cadeiras em que entrei e o campo para digitar o código de uma nova."""
from PySide6.QtWidgets import QDialog, QVBoxLayout

from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario, DialogoTutorial


class TelaTurmas(c.TelaBase):
    def carregar(self):
        turmas = self.janela.turmas.listar_do_aluno()
        self.reiniciar()
        self.botao_entrar = c.botao("+ Entrar em uma turma", "primario", self.entrar)
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.corpo.addLayout(
            c.linha_horizontal(c.rotulo("Minhas turmas", "titulo", quebra=False), None, self.botao_tutorial, self.botao_entrar)
        )
        self.corpo.addWidget(
            c.rotulo("Cada turma é uma cadeira. As suas pesquisas ficam dentro da turma a que pertencem.", "mudo")
        )
        self.linhas = []
        if not turmas:
            self.corpo.addWidget(
                self.vazio("Você ainda não entrou em nenhuma turma. Peça o código ao professor e use “Entrar em uma turma”.")
            )
        else:
            lista = c.Lista()
            for turma in turmas:
                self.linhas.append(lista.adicionar(self._linha(turma)))
            lista.fechar()
            self.corpo.addWidget(lista)
        self.corpo.addStretch(1)

    def _linha(self, turma):
        linha = c.Linha(clicavel=True)
        linha.turma_id = turma.id
        esquerda = QVBoxLayout()
        esquerda.setSpacing(3)
        esquerda.addWidget(c.rotulo(turma.nome, "item", quebra=False))
        esquerda.addWidget(c.rotulo(f"Professor: {turma.professor.nome}", "mudo"))
        linha.selo = c.selo("Grupos permitidos" if turma.permite_grupos else "Só pesquisas individuais", "andamento" if turma.permite_grupos else "neutro")
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addWidget(linha.selo)
        linha.setLayout(conteudo)
        linha.clicado.connect(lambda tid=turma.id: self.janela.abrir_pesquisas(tid))
        return linha

    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "aluno_turmas"))

    def entrar(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Entrar em uma turma",
            [Campo("codigo", "Código da turma", dica="Ex.: K7M2QX")],
            self._entrar,
            rotulo_ok="Entrar na turma",
            subtitulo="O código é gerado pelo professor quando ele cria a turma.",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_pesquisas(self._turma.id)
            self.janela.aviso(f"Você entrou na turma {self._turma.nome}. Crie aqui a sua primeira pesquisa.", "ok")

    def _entrar(self, valores):
        self._turma = self.janela.turmas.entrar(valores["codigo"])
