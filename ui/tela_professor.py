"""Pesquisas dos alunos (professor): a lista de todas as turmas ou só de uma (filtro por turma).

O professor acompanha as que estão em andamento (só leitura), revisa as que foram entregues e
consulta as concluídas. O relatório só abre depois da entrega (RF03, RF23)."""
from PySide6.QtWidgets import QComboBox

from ui import componentes as c
from ui.dialogos import DialogoTutorial
from ui.linhas import linha_de_pesquisa

# (status, título da seção)
SECOES = (
    ("entregue", "Aguardando sua revisão"),
    ("em_andamento", "Em andamento com os alunos"),
    ("concluida", "Concluídas"),
)


class TelaProfessor(c.TelaBase):
    turma_id = None

    def carregar(self, turma_id=None):
        turmas = self.janela.turmas.listar_do_professor()
        if turma_id is not None and turma_id not in {t.id for t in turmas}:
            turma_id = None
        pesquisas = self.janela.revisoes.listar_todas(turma_id)
        self.turma_id = turma_id
        self.reiniciar()

        self.botao_voltar = c.botao("‹ Minhas turmas", "link", self.janela.abrir_turmas_professor)
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.corpo.addLayout(
            c.linha_horizontal(c.rotulo("Pesquisas dos alunos", "titulo", quebra=False), None, self.botao_tutorial)
        )
        self.corpo.addWidget(
            c.rotulo("Acompanhe o que os alunos estão fazendo e revise as pesquisas que eles entregaram.", "mudo")
        )

        # filtro por turma
        self.filtro = QComboBox()
        self.filtro.addItem("Todas as turmas", None)
        for t in turmas:
            self.filtro.addItem(t.nome, t.id)
        self.filtro.setCurrentIndex(self.filtro.findData(turma_id))
        self.filtro.currentIndexChanged.connect(self._filtrar)
        self.corpo.addLayout(c.linha_horizontal(c.rotulo("Turma:", "campo", quebra=False), self.filtro, None))

        self.linhas = []
        self.secoes = {}
        self.titulos_das_secoes = {}
        if not pesquisas:
            self.corpo.addWidget(
                self.vazio(
                    "Nenhum aluno criou uma pesquisa ainda. Quando criarem, elas aparecem aqui."
                    if turma_id is None
                    else "Nenhuma pesquisa nesta turma ainda."
                )
            )
        for status, titulo in SECOES:
            do_status = [p for p in pesquisas if p.status == status]
            self.secoes[status] = []
            if not do_status:
                continue
            cabecalho = c.rotulo(f"{titulo} ({len(do_status)})", "secao", quebra=False)
            self.titulos_das_secoes[status] = cabecalho
            self.corpo.addSpacing(6)
            self.corpo.addWidget(cabecalho)
            lista = c.Lista()
            for p in do_status:
                linha = lista.adicionar(self._linha(p))
                self.linhas.append(linha)
                self.secoes[status].append(linha)
            lista.fechar()
            self.corpo.addWidget(lista)
        self.corpo.addStretch(1)

    def _linha(self, pesquisa):
        return linha_de_pesquisa(
            self.janela, pesquisa, "‹ Pesquisas dos alunos",
            lambda: self.janela.abrir_professor(self.turma_id),
            mostrar_turma=self.turma_id is None,
        )

    def _filtrar(self, _indice):
        self.janela.abrir_professor(self.filtro.currentData())

    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "prof_lista"))
