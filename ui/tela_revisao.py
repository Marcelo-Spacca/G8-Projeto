"""Pesquisa de um aluno vista pelo professor: acompanhar (em andamento) ou revisar (entregue)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout

from services.fonte_service import contar_status
from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario, DialogoTutorial


class TelaRevisao(c.TelaBase):
    pesquisa_id = None

    def carregar(self, pesquisa_id):
        pesquisa = self.janela.revisoes.obter_pesquisa(pesquisa_id)
        self.pesquisa_id = pesquisa.id
        self.pesquisa = pesquisa
        self.interacoes = pesquisa.interacoes
        em_revisao = pesquisa.status == "entregue"
        entregue = pesquisa.status in ("entregue", "concluida")
        self.reiniciar()

        self.botao_voltar = c.botao(
            f"‹ {pesquisa.turma.nome}", "link", lambda: self.janela.abrir_turma_professor(pesquisa.turma_id)
        )
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.selo = c.selo_da_pesquisa(pesquisa, "professor")
        self.corpo.addLayout(c.linha_horizontal(self.selo, None))
        self.titulo = c.rotulo(pesquisa.titulo, "titulo", selecionavel=True)
        self.corpo.addWidget(self.titulo)
        if pesquisa.de_grupo:
            self.autor = c.rotulo(f"Grupo {pesquisa.grupo.nome}  ·  integrantes: {c.nomes(pesquisa.grupo.alunos)}", "mudo")
        else:
            self.autor = c.rotulo(f"Aluno: {pesquisa.aluno.nome}", "mudo")
        self.corpo.addWidget(self.autor)
        self.corpo.addWidget(c.rotulo(f"Turma: {pesquisa.turma.nome}", "mudo"))
        self.corpo.addWidget(c.rotulo(pesquisa.objetivo, "documento", selecionavel=True))
        self.recado = self._recado_de_estado(pesquisa)
        self.corpo.addWidget(self.recado)

        self.botao_relatorio = c.botao("Ver relatório", ao_clicar=self.ver_relatorio)
        self.botao_relatorio.setEnabled(entregue)
        if not entregue:
            self.botao_relatorio.setToolTip("O relatório fica disponível quando o aluno entregar a pesquisa.")
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.botao_aceitar = c.botao("Aceitar pesquisa", "primario", self.aceitar)
        self.botao_devolver = c.botao("Devolver ao aluno", "perigo", self.devolver)
        acoes = [self.botao_relatorio, self.botao_tutorial]
        if em_revisao:
            acoes += [None, self.botao_devolver, self.botao_aceitar]
        self.corpo.addLayout(c.linha_horizontal(*acoes))
        self.corpo.addSpacing(10)

        self.corpo.addWidget(c.rotulo("Interações com IA", "secao", quebra=False))
        self.linhas = []
        if not self.interacoes:
            self.corpo.addWidget(self.vazio("O aluno ainda não registrou nenhuma interação."))
        else:
            lista = c.Lista()
            for i in self.interacoes:
                self.linhas.append(lista.adicionar(self._linha(i)))
            lista.fechar()
            self.corpo.addWidget(lista)
        self.corpo.addStretch(1)

    @staticmethod
    def _recado_de_estado(pesquisa):
        if pesquisa.status == "entregue":
            return c.recado(
                f"Entregue em {c.formatar_data(pesquisa.data_entrega)}: aguardando a sua revisão",
                "Abra cada interação para julgar as fontes, comentar e confirmar. "
                "Depois, aceite a pesquisa ou devolva-a ao aluno com uma mensagem.",
                "aviso",
            )
        if pesquisa.status == "concluida":
            return c.recado(
                f"Concluída em {c.formatar_data(pesquisa.data_conclusao)}",
                "Você aceitou esta pesquisa. Ela não pode mais ser alterada.",
                "ok",
            )
        if pesquisa.devolvida:
            return c.recado(
                f"Devolvida ao aluno em {c.formatar_data(pesquisa.data_devolucao)}",
                f"Sua mensagem: {pesquisa.mensagem_devolucao}\n\nO aluno está ajustando. Você acompanha o que ele faz; a revisão volta quando ele entregar de novo.",
                "devolucao",
            )
        return c.recado(
            "Em andamento com o aluno",
            "Você pode acompanhar o que ele registrou, mas só consegue revisar depois que ele entregar a pesquisa.",
            "info",
        )

    def _linha(self, interacao):
        linha = c.Linha(clicavel=True)
        linha.interacao_id = interacao.id
        esquerda = QVBoxLayout()
        esquerda.setSpacing(4)
        esquerda.addLayout(
            c.linha_horizontal(
                c.selo(interacao.ferramenta_ia, "neutro"),
                c.rotulo(c.formatar_data(interacao.data_registro), "dica", quebra=False),
                None,
            )
        )
        esquerda.addWidget(c.rotulo(c.cortar(interacao.pergunta, 140), "documento"))
        resumo = c.rotulo(c.resumo_fontes(contar_status(interacao.fontes)), "mudo", quebra=False)
        selos = []
        if interacao.confirmada:
            selos.append(c.selo("Confirmada", "verificada"))
        if interacao.comentario_professor:
            selos.append(c.selo("Comentada", "andamento"))
        linha.selos = selos
        lateral = QVBoxLayout()
        lateral.setSpacing(5)
        lateral.addWidget(resumo, 0, Qt.AlignRight)
        if selos:
            lateral.addLayout(c.linha_horizontal(None, *selos, espaco=6))
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(lateral)
        linha.setLayout(conteudo)
        linha.resumo_fontes = resumo
        linha.clicado.connect(lambda iid=interacao.id: self.janela.abrir_revisao_interacao(iid))
        return linha

    # ------------------------------------------------------------ ações
    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "prof_pesquisa"))

    def ver_relatorio(self):
        self.janela.abrir_relatorio(
            self.pesquisa_id, "‹ Voltar para a pesquisa", lambda: self.janela.abrir_revisao(self.pesquisa_id)
        )

    def aceitar(self):
        pendentes = sum(contar_status(i.fontes)["nao_verificada"] for i in self.interacoes)
        abertas = sum(1 for i in self.interacoes if not i.confirmada)
        texto = "A pesquisa ficará concluída e não poderá mais ser alterada pelo aluno nem por você."
        if abertas:
            texto = f"{c.plural(abertas, 'interação ainda não confirmada será fechada', 'interações ainda não confirmadas serão fechadas')}. " + texto
        if pendentes:
            texto = f"Ainda há {c.plural(pendentes, 'fonte', 'fontes')} sem julgamento. " + texto
        if not c.perguntar(self.janela, "Aceitar esta pesquisa?", texto, "Aceitar pesquisa"):
            return
        if self.janela.tentar(self.janela.revisoes.aceitar, self.pesquisa_id) is self.janela.FALHOU:
            return
        self.janela.abrir_revisao(self.pesquisa_id)
        self.janela.aviso("Pesquisa aceita e concluída.", "ok")

    def devolver(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Devolver pesquisa ao aluno",
            [Campo("mensagem", "Mensagem para o aluno", "texto", altura=130, dica="Explique por que a pesquisa não foi aceita e o que ajustar.")],
            lambda v: self.janela.revisoes.devolver(self.pesquisa_id, v["mensagem"]),
            subtitulo="A pesquisa volta a “em andamento” para o aluno ajustar, e ele lê esta mensagem no sistema. "
            "Interações que você confirmou continuam fechadas.",
            rotulo_ok="Devolver ao aluno",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_revisao(self.pesquisa_id)
            self.janela.aviso("Pesquisa devolvida ao aluno com a sua mensagem.", "ok")
