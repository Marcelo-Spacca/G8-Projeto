"""Uma turma vista pelo professor: código, lista de alunos com as pesquisas de cada um e grupos."""
from PySide6.QtWidgets import QDialog, QFrame, QVBoxLayout

from ui import componentes as c
from ui.dialogos import DialogoEscolherAluno, DialogoTutorial
from ui.linhas import linha_de_pesquisa


class TelaTurmaProfessor(c.TelaBase):
    turma_id = None
    visao = "alunos"

    def carregar(self, turma_id, visao="alunos"):
        turma = self.janela.turmas.obter_do_professor(turma_id)
        if visao == "grupos" and not turma.permite_grupos:
            visao = "alunos"
        self.turma_id, self.turma, self.visao = turma.id, turma, visao
        self.reiniciar()

        self.botao_voltar = c.botao("‹ Minhas turmas", "link", self.janela.abrir_turmas_professor)
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.corpo.addWidget(c.rotulo(turma.nome, "titulo", quebra=False))
        self.codigo = c.rotulo(turma.codigo, "codigo", quebra=False, selecionavel=True)
        self.selo_grupos = c.selo("Grupos permitidos" if turma.permite_grupos else "Grupos desativados", "andamento" if turma.permite_grupos else "neutro")
        self.corpo.addLayout(c.linha_horizontal(
            c.rotulo("Código de entrada:", "mudo", quebra=False), self.codigo, self.selo_grupos, None, espaco=10
        ))

        self.aba_alunos = c.aba("Alunos", visao == "alunos", lambda: self.janela.abrir_turma_professor(turma_id, "alunos"))
        self.aba_grupos = c.aba("Grupos", visao == "grupos", lambda: self.janela.abrir_turma_professor(turma_id, "grupos"))
        self.botao_pesquisas = c.botao("Lista de pesquisas", ao_clicar=lambda: self.janela.abrir_professor(turma_id))
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        if not turma.permite_grupos:
            self.aba_grupos.setEnabled(False)
            self.aba_grupos.setToolTip("Você não habilitou grupos ao criar esta turma.")
        self.corpo.addLayout(c.linha_horizontal(self.aba_alunos, self.aba_grupos, None, self.botao_pesquisas, self.botao_tutorial, espaco=8))

        self.linhas = []       # linhas de pesquisa (qualquer aba)
        self.blocos = []       # um por aluno (aba Alunos) ou por grupo (aba Grupos)
        if visao == "grupos":
            self._montar_grupos(turma)
        else:
            self._montar_alunos(turma)
        self.corpo.addStretch(1)

    # ------------------------------------------------------------ aba Alunos
    def _linha_de_pesquisa(self, pesquisa, **opcoes):
        linha = linha_de_pesquisa(
            self.janela, pesquisa, f"‹ {self.turma.nome}",
            lambda: self.janela.abrir_turma_professor(self.turma_id, self.visao), **opcoes,
        )
        self.linhas.append(linha)
        return linha

    def _montar_alunos(self, turma):
        alunos = turma.alunos
        if not alunos:
            self.corpo.addWidget(self.vazio(
                f"Nenhum aluno entrou ainda. Passe o código {turma.codigo} para a turma."
            ))
            return
        self.corpo.addWidget(c.rotulo(
            c.plural(len(alunos), "aluno matriculado", "alunos matriculados") + ". Cada um aparece com as próprias pesquisas.", "mudo"
        ))
        grupos_do_aluno = {a.id: [] for a in alunos}
        for g in turma.grupos:
            for a in g.alunos:
                grupos_do_aluno.setdefault(a.id, []).append(g.nome)
        for aluno in alunos:
            proprias = sorted(
                (p for p in turma.pesquisas if p.aluno_id == aluno.id),
                key=lambda p: (p.data_entrega or p.data_criacao, p.id), reverse=True,
            )
            bloco = QFrame()
            bloco.aluno_id = aluno.id
            v = QVBoxLayout(bloco)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(6)
            bloco.cabecalho = c.rotulo(f"{aluno.nome}  ({c.plural(len(proprias), 'pesquisa', 'pesquisas')})", "secao", quebra=False)
            v.addWidget(bloco.cabecalho)
            em_grupos = grupos_do_aluno.get(aluno.id)
            bloco.grupos = None
            if em_grupos:
                bloco.grupos = c.rotulo("Em grupos: " + ", ".join(sorted(em_grupos)), "dica")
                v.addWidget(bloco.grupos)
            bloco.linhas = []
            if proprias:
                lista = c.Lista()
                for p in proprias:
                    bloco.linhas.append(lista.adicionar(self._linha_de_pesquisa(p, mostrar_autor=False)))
                lista.fechar()
                v.addWidget(lista)
            else:
                bloco.vazio = c.rotulo("Ainda não criou pesquisa individual.", "dica")
                v.addWidget(bloco.vazio)
            self.blocos.append(bloco)
            self.corpo.addSpacing(4)
            self.corpo.addWidget(bloco)

    # ------------------------------------------------------------ aba Grupos
    def _montar_grupos(self, turma):
        if not turma.grupos:
            self.corpo.addWidget(self.vazio("Nenhum grupo foi criado ainda. Os alunos criam grupos na turma e convidam os colegas; você também pode atribuir alunos depois."))
            return
        em_algum = {a.id for g in turma.grupos for a in g.alunos}
        sem_grupo = [a for a in turma.alunos if a.id not in em_algum]
        self.sem_grupo = None
        if sem_grupo:
            self.sem_grupo = c.rotulo("Alunos sem grupo: " + c.nomes(sem_grupo) + ".", "mudo")
            self.corpo.addWidget(self.sem_grupo)
        for grupo in sorted(turma.grupos, key=lambda g: (g.nome.lower(), g.id)):
            self.blocos.append(self._bloco_do_grupo(turma, grupo))
            self.corpo.addSpacing(4)
            self.corpo.addWidget(self.blocos[-1])

    def _bloco_do_grupo(self, turma, grupo):
        bloco = QFrame()
        bloco.setProperty("papel", "painel")
        bloco.grupo_id = grupo.id
        v = QVBoxLayout(bloco)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)
        bloco.botao_atribuir = c.botao("+ Atribuir aluno", ao_clicar=lambda g=grupo: self.atribuir(g))
        bloco.cabecalho = c.rotulo(f"Grupo {grupo.nome}", "secao", quebra=False)
        v.addLayout(c.linha_horizontal(bloco.cabecalho, None, bloco.botao_atribuir))
        v.addWidget(c.rotulo(f"Pesquisa do grupo: {grupo.titulo}", "mudo"))
        bloco.integrantes = {}
        for aluno in grupo.alunos:
            remover = c.botao("Remover", "perigo", lambda g=grupo, a=aluno: self.remover(g, a))
            linha = c.linha_horizontal(c.rotulo(aluno.nome, "documento", quebra=False), None, remover)
            bloco.integrantes[aluno.id] = remover
            v.addLayout(linha)
        bloco.linhas = []
        if grupo.pesquisa is not None:
            pesquisa = next((p for p in turma.pesquisas if p.id == grupo.pesquisa.id), grupo.pesquisa)
            lista = c.Lista()
            bloco.linhas.append(lista.adicionar(self._linha_de_pesquisa(pesquisa, mostrar_autor=False)))
            lista.fechar()
            v.addWidget(lista)
        else:
            bloco.sem_pesquisa = c.rotulo(
                "Ainda sem pesquisa: ela é criada quando o grupo tiver dois integrantes.", "dica"
            )
            v.addWidget(bloco.sem_pesquisa)
        return bloco

    # ------------------------------------------------------------ ações
    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "prof_turma"))

    def atribuir(self, grupo):
        ocupados = {a.id for a in grupo.alunos}
        candidatos = [a for a in self.turma.alunos if a.id not in ocupados]
        if not candidatos:
            self.janela.aviso("Todos os alunos da turma já estão neste grupo.", "info")
            return
        dialogo = DialogoEscolherAluno(
            self.janela, grupo, candidatos,
            lambda v: self.janela.grupos.atribuir_aluno(grupo.id, v["aluno_id"]),
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_turma_professor(self.turma_id, "grupos")
            self.janela.aviso("Aluno atribuído ao grupo.", "ok")

    def remover(self, grupo, aluno):
        texto = f"{aluno.nome} deixa o grupo {grupo.nome} e perde o acesso à pesquisa dele. O que o grupo já registrou continua com o grupo."
        if not c.perguntar(self.janela, "Remover aluno do grupo?", texto, "Remover do grupo", perigo=True):
            return
        if self.janela.tentar(self.janela.grupos.remover_aluno, grupo.id, aluno.id) is self.janela.FALHOU:
            return
        self.janela.abrir_turma_professor(self.turma_id, "grupos")
        self.janela.aviso(f"{aluno.nome} foi removido do grupo.", "ok")
