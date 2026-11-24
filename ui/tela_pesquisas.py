"""Uma turma vista pelo aluno: suas pesquisas individuais (RF06/RF07) e as pesquisas do grupo.

Duas abas (Individuais | Grupos). "Nova pesquisa" só existe nas individuais e "Criar grupo" só na
aba de grupos. Se a turma não permite grupos, a aba e o botão de convites ficam cinza."""
from PySide6.QtWidgets import QDialog, QVBoxLayout

from ui import componentes as c
from ui.dialogos import Campo, DialogoConvidar, DialogoConvites, DialogoFormulario, DialogoTutorial


class TelaPesquisas(c.TelaBase):
    turma_id = None
    visao = "individuais"

    def carregar(self, turma_id, visao="individuais"):
        turma = self.janela.turmas.obter_do_aluno(turma_id)
        permite = turma.permite_grupos
        if visao == "grupos" and not permite:
            visao = "individuais"
        convites = self.janela.grupos.convites_pendentes(turma_id) if permite else []
        if visao == "grupos":
            grupos = self.janela.grupos.listar_do_aluno(turma_id)
            pesquisas = []
        else:
            grupos = []
            pesquisas = self.janela.pesquisas.listar_minhas(turma_id)
        self.turma_id, self.turma, self.visao = turma.id, turma, visao
        self.convites = convites
        self.reiniciar()

        self.botao_voltar = c.botao("‹ Minhas turmas", "link", self.janela.abrir_turmas)
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.corpo.addWidget(c.rotulo(turma.nome, "titulo", quebra=False))
        self.corpo.addWidget(c.rotulo(f"Professor: {turma.professor.nome}", "mudo"))

        # abas + convites + tutorial
        self.aba_individuais = c.aba("Individuais", visao == "individuais", lambda: self.janela.abrir_pesquisas(turma_id, "individuais"))
        self.aba_grupos = c.aba("Grupos", visao == "grupos", lambda: self.janela.abrir_pesquisas(turma_id, "grupos"))
        self.botao_convites = c.botao(f"Convites ({len(convites)})" if convites else "Convites", ao_clicar=self.ver_convites)
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        if not permite:
            for b in (self.aba_grupos, self.botao_convites):
                b.setEnabled(False)
                b.setToolTip("O professor não habilitou grupos nesta turma.")
        self.corpo.addLayout(c.linha_horizontal(self.aba_individuais, self.aba_grupos, None, self.botao_convites, self.botao_tutorial, espaco=8))

        self.botao_nova = c.botao("+ Nova pesquisa", "primario", self.nova_pesquisa)
        self.botao_criar_grupo = c.botao("+ Criar grupo", "primario", self.criar_grupo)
        if visao == "grupos":
            self.corpo.addLayout(c.linha_horizontal(
                c.rotulo("Pesquisas feitas em grupo: todos os integrantes trabalham na mesma pesquisa.", "mudo"),
                self.botao_criar_grupo,
            ))
        else:
            self.corpo.addLayout(c.linha_horizontal(
                c.rotulo("Cada pesquisa reúne as interações com IA de um trabalho seu.", "mudo"),
                self.botao_nova,
            ))

        self.linhas = []
        if visao == "grupos":
            self._montar_grupos(grupos)
        else:
            self._montar_individuais(pesquisas)
        self.corpo.addStretch(1)

    # ------------------------------------------------------------ listas
    def _montar_individuais(self, pesquisas):
        if not pesquisas:
            self.corpo.addWidget(self.vazio("Você ainda não criou nenhuma pesquisa nesta turma. Crie a primeira para começar a registrar o uso de IA do seu trabalho."))
            return
        lista = c.Lista()
        for p in pesquisas:
            self.linhas.append(lista.adicionar(self._linha(p)))
        lista.fechar()
        self.corpo.addWidget(lista)

    def _montar_grupos(self, grupos):
        if not grupos:
            self.corpo.addWidget(self.vazio("Você ainda não faz parte de nenhum grupo nesta turma. Crie um grupo e convide colegas, ou aceite um convite."))
            return
        lista = c.Lista()
        for g in grupos:
            self.linhas.append(lista.adicionar(self._linha_do_grupo(g)))
        lista.fechar()
        self.corpo.addWidget(lista)

    def _linha(self, pesquisa):
        linha = c.Linha(clicavel=True)
        linha.pesquisa_id = pesquisa.id
        esquerda = QVBoxLayout()
        esquerda.setSpacing(3)
        esquerda.addWidget(c.rotulo(pesquisa.titulo, "item", quebra=False))
        esquerda.addWidget(c.rotulo(c.cortar(pesquisa.objetivo, 120), "mudo"))
        direita = QVBoxLayout()
        direita.setSpacing(4)
        selo = c.selo_da_pesquisa(pesquisa)
        linha.selo = selo
        direita.addWidget(selo)
        direita.addWidget(c.rotulo(f"Criada em {c.formatar_dia(pesquisa.data_criacao)}", "dica", quebra=False))
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(direita)
        linha.setLayout(conteudo)
        linha.clicado.connect(lambda pid=pesquisa.id: self.janela.abrir_pesquisa(pid))
        return linha

    def _linha_do_grupo(self, grupo):
        """Grupo com pesquisa: linha clicável. Grupo ainda sem pesquisa: aguarda o primeiro aceite."""
        pesquisa = grupo.pesquisa
        linha = c.Linha(clicavel=pesquisa is not None)
        linha.grupo_id = grupo.id
        linha.pesquisa_id = pesquisa.id if pesquisa else None
        esquerda = QVBoxLayout()
        esquerda.setSpacing(3)
        esquerda.addWidget(c.rotulo(grupo.titulo, "item", quebra=False))
        esquerda.addWidget(c.rotulo(f"Grupo {grupo.nome}  ·  {c.nomes(grupo.alunos)}", "mudo"))
        direita = QVBoxLayout()
        direita.setSpacing(4)
        linha.botao_convidar = None
        if pesquisa is not None:
            linha.selo = c.selo_da_pesquisa(pesquisa)
            direita.addWidget(linha.selo)
            direita.addWidget(c.rotulo(f"Criada em {c.formatar_dia(pesquisa.data_criacao)}", "dica", quebra=False))
            linha.clicado.connect(lambda pid=pesquisa.id: self.janela.abrir_pesquisa(pid))
        else:
            pendentes = sum(1 for cv in grupo.convites if cv.status == "pendente")
            linha.selo = c.selo("Aguardando integrantes", "pendente")
            esquerda.addWidget(c.rotulo(
                "A pesquisa do grupo é criada quando o primeiro convidado aceitar."
                + (f" {c.plural(pendentes, 'convite pendente', 'convites pendentes')}." if pendentes else ""),
                "dica",
            ))
            linha.botao_convidar = c.botao("Convidar alunos", ao_clicar=lambda g=grupo: self.convidar(g))
            direita.addWidget(linha.selo)
            direita.addWidget(linha.botao_convidar)
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(direita)
        linha.setLayout(conteudo)
        return linha

    # ------------------------------------------------------------ ações
    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "aluno_pesquisas"))

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
            subtitulo=f"Turma: {self.turma.nome}",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_pesquisa(self._criada.id)
            self.janela.aviso("Pesquisa criada. Registre a primeira interação com a IA.", "ok")

    def _criar(self, valores):
        self._criada = self.janela.pesquisas.criar(self.turma_id, valores["titulo"], valores["objetivo"])

    def criar_grupo(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Criar grupo",
            [
                Campo("nome", "Nome do grupo", dica="Ex.: Time Alfa"),
                Campo("titulo", "Título da pesquisa do grupo", dica="Ex.: Impactos da IA na educação"),
                Campo("objetivo", "Objetivo: o que o grupo quer descobrir?", "texto", altura=100),
            ],
            self._criar_grupo,
            rotulo_ok="Criar grupo",
            subtitulo="Depois de criar, você convida colegas da turma. A pesquisa é do grupo, não de um aluno só.",
        )
        if c.abrir(dialogo) != QDialog.Accepted:
            return
        grupo = self._grupo_criado
        self.janela.abrir_pesquisas(self.turma_id, "grupos")
        candidatos = self.janela.tentar(self.janela.grupos.convidaveis, grupo.id)
        if candidatos is self.janela.FALHOU or not candidatos:
            self.janela.aviso("Grupo criado. Ainda não há outros alunos na turma para convidar.", "info")
            return
        self.janela.aviso("Grupo criado. Agora convide os colegas.", "ok")
        self.convidar(grupo)

    def _criar_grupo(self, valores):
        self._grupo_criado = self.janela.grupos.criar(
            self.turma_id, valores["nome"], valores["titulo"], valores["objetivo"]
        )

    def convidar(self, grupo):
        candidatos = self.janela.tentar(self.janela.grupos.convidaveis, grupo.id)
        if candidatos is self.janela.FALHOU:
            return
        if not candidatos:
            self.janela.aviso("Não há mais colegas da turma para convidar: todos já estão no grupo ou têm convite pendente.", "info")
            return
        dialogo = DialogoConvidar(
            self.janela, grupo, candidatos,
            lambda v: self.janela.grupos.convidar(grupo.id, v["alunos_ids"]),
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_pesquisas(self.turma_id, "grupos")
            self.janela.aviso("Convites enviados. Quando alguém aceitar, a pesquisa do grupo aparece aqui.", "ok")

    def ver_convites(self):
        dialogo = DialogoConvites(self.janela, self.convites, lambda cid, ok: self.janela.grupos.responder_convite(cid, ok))
        c.abrir(dialogo)
        aceitos = [nome for nome, ok in dialogo.respostas if ok]
        self.janela.abrir_pesquisas(self.turma_id, "grupos" if aceitos else self.visao)
        if aceitos:
            self.janela.aviso(f"Você entrou no grupo {aceitos[-1]}. A pesquisa do grupo já está na lista.", "ok")
        elif dialogo.respostas:
            self.janela.aviso("Convite recusado.", "info")
