"""Minhas turmas (professor): criar turma (gera o código de entrada), ver e excluir turmas."""
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QDialog, QVBoxLayout

from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario, DialogoTutorial


class TelaTurmasProfessor(c.TelaBase):
    def carregar(self):
        turmas = self.janela.turmas.listar_do_professor()
        self.reiniciar()
        self.botao_nova = c.botao("+ Nova turma", "primario", self.nova_turma)
        self.botao_pesquisas = c.botao("Pesquisas de todas as turmas", ao_clicar=self.janela.abrir_professor)
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.corpo.addLayout(
            c.linha_horizontal(c.rotulo("Minhas turmas", "titulo", quebra=False), None, self.botao_tutorial, self.botao_nova)
        )
        self.corpo.addWidget(
            c.rotulo("Crie uma turma para cada cadeira e passe o código aos alunos. Dentro dela você vê os alunos, os grupos e as pesquisas.", "mudo")
        )
        self.corpo.addLayout(c.linha_horizontal(self.botao_pesquisas, None))
        self.linhas = []
        if not turmas:
            self.corpo.addWidget(self.vazio("Você ainda não criou nenhuma turma. Crie a primeira: o sistema gera o código de entrada para os alunos."))
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
        linha.turma = turma
        aguardando = sum(1 for p in turma.pesquisas if p.status == "entregue")
        partes = [
            c.plural(len(turma.matriculas), "aluno", "alunos"),
            c.plural(len(turma.pesquisas), "pesquisa", "pesquisas"),
        ]
        if turma.permite_grupos:
            partes.append(c.plural(len(turma.grupos), "grupo", "grupos"))
        esquerda = QVBoxLayout()
        esquerda.setSpacing(4)
        linha.selo = c.selo("Grupos permitidos" if turma.permite_grupos else "Só individuais", "andamento" if turma.permite_grupos else "neutro")
        esquerda.addLayout(c.linha_horizontal(c.rotulo(turma.nome, "item", quebra=False), linha.selo, None, espaco=10))
        esquerda.addWidget(c.rotulo("  ·  ".join(partes), "mudo"))
        linha.aguardando = None
        if aguardando:
            linha.aguardando = c.selo(f"{aguardando} aguardando revisão", "pendente")
            esquerda.addLayout(c.linha_horizontal(linha.aguardando, None))

        meio = QVBoxLayout()
        meio.setSpacing(4)
        meio.addWidget(c.rotulo("Código de entrada", "dica", quebra=False))
        linha.codigo = c.rotulo(turma.codigo, "codigo", quebra=False, selecionavel=True)
        meio.addWidget(linha.codigo)

        linha.botao_copiar = c.botao("Copiar código", ao_clicar=lambda t=turma: self.copiar(t))
        linha.botao_excluir = c.botao("Excluir", "perigo", lambda t=turma: self.excluir(t))
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(meio)
        conteudo.addWidget(linha.botao_copiar)
        conteudo.addWidget(linha.botao_excluir)
        linha.setLayout(conteudo)
        linha.clicado.connect(lambda tid=turma.id: self.janela.abrir_turma_professor(tid))
        return linha

    # ------------------------------------------------------------ ações
    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "prof_turmas"))

    def nova_turma(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Nova turma",
            [
                Campo("nome", "Nome da turma (a cadeira)", dica="Ex.: Projeto 1, SI 26.2"),
                Campo("permite_grupos", "Permitir que os alunos criem grupos nesta turma", "caixa"),
            ],
            self._criar,
            rotulo_ok="Criar turma",
            subtitulo="Ao criar, o sistema gera um código de entrada. Quem tiver o código entra na turma.",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_turma_professor(self._criada.id)
            self.janela.aviso(f"Turma criada. Código de entrada: {self._criada.codigo}. Passe-o aos alunos.", "ok")

    def _criar(self, valores):
        self._criada = self.janela.turmas.criar(valores["nome"], valores["permite_grupos"])

    def copiar(self, turma):
        QGuiApplication.clipboard().setText(turma.codigo)
        self.janela.aviso(f"Código {turma.codigo} copiado.", "ok")

    def excluir(self, turma):
        n_alunos, n_pesquisas = len(turma.matriculas), len(turma.pesquisas)
        texto = (
            f"A turma “{turma.nome}”, com {c.plural(n_alunos, 'aluno matriculado', 'alunos matriculados')}, "
            f"{c.plural(n_pesquisas, 'pesquisa', 'pesquisas')} e os grupos, será apagada com todas as interações, "
            "fontes e relatórios. O código deixa de valer. Isso não pode ser desfeito."
        )
        if not c.perguntar(self.janela, "Excluir esta turma?", texto, "Excluir turma", perigo=True):
            return
        if self.janela.tentar(self.janela.turmas.excluir, turma.id) is self.janela.FALHOU:
            return
        self.janela.abrir_turmas_professor()
        self.janela.aviso("Turma excluída.", "ok")
