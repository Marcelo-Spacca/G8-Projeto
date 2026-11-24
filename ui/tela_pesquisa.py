"""Detalhe da pesquisa: interações (RF11, RF12), editar (RF08), entregar ao professor (RF10) e relatório (RF21)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout

from services.fonte_service import contar_status
from ui import componentes as c
from ui.dialogos import Campo, DialogoConvidar, DialogoFormulario, DialogoTutorial


class TelaPesquisa(c.TelaBase):
    pesquisa_id = None

    def carregar(self, pesquisa_id):
        pesquisa = self.janela.pesquisas.obter(pesquisa_id)
        interacoes = self.janela.interacoes.listar(pesquisa_id)
        self.pesquisa_id = pesquisa.id
        self.pesquisa = pesquisa
        self.interacoes = interacoes
        aberta = pesquisa.status == "em_andamento"
        self.reiniciar()

        visao = "grupos" if pesquisa.de_grupo else "individuais"
        self.botao_voltar = c.botao(
            f"‹ {pesquisa.turma.nome}", "link", lambda: self.janela.abrir_pesquisas(pesquisa.turma_id, visao)
        )
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.titulo = c.rotulo(pesquisa.titulo, "titulo", selecionavel=True)
        self.selo = c.selo_da_pesquisa(pesquisa)
        self.corpo.addLayout(c.linha_horizontal(self.selo, None))
        self.corpo.addWidget(self.titulo)
        self.integrantes = None
        if pesquisa.de_grupo:
            self.integrantes = c.rotulo(
                f"Grupo {pesquisa.grupo.nome}  ·  integrantes: {c.nomes(pesquisa.grupo.alunos)}", "mudo"
            )
            self.corpo.addWidget(self.integrantes)
        self.corpo.addWidget(c.rotulo(pesquisa.objetivo, "documento", selecionavel=True))
        self.recado = self._recado_de_estado(pesquisa)
        if self.recado is not None:
            self.corpo.addWidget(self.recado)

        self.botao_editar = c.botao("Editar título e objetivo", ao_clicar=self.editar)
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.botao_relatorio = c.botao(
            "Ver relatório" if not aberta else "Ver prévia do relatório", ao_clicar=self.ver_relatorio
        )
        self.botao_entregar = c.botao("Entregar para o professor", "primario", self.entregar)
        self.botao_excluir = c.botao("Excluir pesquisa", "perigo", self.excluir)
        self.botao_convidar = c.botao("Convidar alunos", ao_clicar=self.convidar)
        if aberta:
            acoes = [self.botao_editar, self.botao_tutorial, self.botao_relatorio]
            if pesquisa.de_grupo:
                acoes.append(self.botao_convidar)
            acoes += [self.botao_entregar, None]
            if not pesquisa.de_grupo:  # pesquisa de grupo não é excluída pelos alunos
                acoes.append(self.botao_excluir)
        else:
            acoes = [self.botao_relatorio, self.botao_tutorial]
        self.corpo.addLayout(c.linha_horizontal(*acoes))
        self.corpo.addSpacing(10)

        self.botao_nova_interacao = c.botao("+ Nova interação", "primario", self.nova_interacao)
        cabecalho = [c.rotulo("Interações com IA", "secao", quebra=False), None]
        if aberta:
            cabecalho.append(self.botao_nova_interacao)
        self.corpo.addLayout(c.linha_horizontal(*cabecalho))

        self.linhas = []
        if not interacoes:
            self.corpo.addWidget(self.vazio("Nenhuma interação registrada ainda. Anote a ferramenta, a pergunta e a resposta de cada conversa com a IA." if aberta else "Nenhuma interação foi registrada."))
        else:
            lista = c.Lista()
            for i in interacoes:
                self.linhas.append(lista.adicionar(self._linha(i)))
            lista.fechar()
            self.corpo.addWidget(lista)
        self.corpo.addStretch(1)

    @staticmethod
    def _recado_de_estado(pesquisa):
        """Explica ao aluno em que pé está a pesquisa e, se devolvida, mostra a mensagem do professor."""
        if pesquisa.devolvida:
            return c.recado(
                f"O professor devolveu esta pesquisa em {c.formatar_data(pesquisa.data_devolucao)}",
                pesquisa.mensagem_devolucao
                + "\n\nAjuste o que ele pediu e use “Entregar para o professor” de novo. "
                "Interações que ele já confirmou continuam fechadas.",
                "devolucao",
            )
        if pesquisa.status == "entregue":
            return c.recado(
                f"Entregue ao professor em {c.formatar_data(pesquisa.data_entrega)}",
                "Ele está revisando. Você não pode alterar nada até ele aceitar ou devolver a pesquisa.",
                "aviso",
            )
        if pesquisa.status == "concluida":
            return c.recado(
                f"Concluída pelo professor em {c.formatar_data(pesquisa.data_conclusao)}",
                "A pesquisa foi aceita. Ela e o relatório não podem mais ser alterados.",
                "ok",
            )
        return None

    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "aluno_pesquisa"))

    def excluir(self):  # RF09
        n = len(self.interacoes)
        extra = f" e {c.plural(n, 'interação registrada', 'interações registradas')}, com as fontes e os trechos," if n else ""
        texto = f"A pesquisa “{c.cortar(self.pesquisa.titulo, 60)}”{extra} serão apagadas. Isso não pode ser desfeito."
        if not c.perguntar(self.janela, "Excluir esta pesquisa?", texto, "Excluir", perigo=True):
            return
        if self.janela.tentar(self.janela.pesquisas.excluir, self.pesquisa_id) is self.janela.FALHOU:
            return
        self.janela.abrir_pesquisas(self.pesquisa.turma_id)
        self.janela.aviso("Pesquisa excluída.", "ok")

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
        resumo = c.resumo_fontes(contar_status(interacao.fontes))
        direita = c.rotulo(resumo, "mudo", quebra=False)
        selos = []
        if interacao.confirmada:
            selos.append(c.selo("Confirmada", "verificada"))
        if interacao.comentario_professor:
            selos.append(c.selo("Comentário do professor", "andamento"))
        linha.selos = selos
        lateral = QVBoxLayout()
        lateral.setSpacing(5)
        lateral.addWidget(direita, 0, Qt.AlignRight)
        if selos:
            lateral.addLayout(c.linha_horizontal(None, *selos, espaco=6))
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addLayout(lateral)
        linha.setLayout(conteudo)
        linha.resumo_fontes = direita
        linha.clicado.connect(lambda iid=interacao.id: self.janela.abrir_interacao(iid))
        return linha

    # ------------------------------------------------------------ ações
    def nova_interacao(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Nova interação",
            [
                Campo("ferramenta", "Ferramenta de IA usada", dica="Ex.: ChatGPT, Claude, Gemini"),
                Campo("pergunta", "Pergunta feita", "texto", altura=100),
                Campo("resposta", "Resposta obtida", "texto", altura=140),
            ],
            self._registrar,
            rotulo_ok="Salvar interação",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_interacao(self._registrada.id)
            self.janela.aviso("Interação registrada. Cadastre as fontes que a IA citou.", "ok")

    def _registrar(self, valores):
        self._registrada = self.janela.interacoes.registrar(
            self.pesquisa_id, valores["ferramenta"], valores["pergunta"], valores["resposta"]
        )

    def editar(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Editar pesquisa",
            [Campo("titulo", "Título"), Campo("objetivo", "Objetivo", "texto", altura=100)],
            lambda v: self.janela.pesquisas.editar(self.pesquisa_id, v["titulo"], v["objetivo"]),
            valores={"titulo": self.pesquisa.titulo, "objetivo": self.pesquisa.objetivo},
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_pesquisa(self.pesquisa_id)
            self.janela.aviso("Pesquisa atualizada.", "ok")

    def convidar(self):
        candidatos = self.janela.tentar(self.janela.grupos.convidaveis, self.pesquisa.grupo_id)
        if candidatos is self.janela.FALHOU:
            return
        if not candidatos:
            self.janela.aviso("Não há mais colegas da turma para convidar: todos já estão no grupo ou têm convite pendente.", "info")
            return
        grupo = self.pesquisa.grupo
        dialogo = DialogoConvidar(
            self.janela, grupo, candidatos,
            lambda v: self.janela.grupos.convidar(grupo.id, v["alunos_ids"]),
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_pesquisa(self.pesquisa_id)
            self.janela.aviso("Convites enviados.", "ok")

    def ver_relatorio(self):
        self.janela.abrir_relatorio(self.pesquisa_id, "‹ Voltar para a pesquisa", lambda: self.janela.abrir_pesquisa(self.pesquisa_id))

    def entregar(self):  # RF10
        pendentes = sum(contar_status(i.fontes)["nao_verificada"] for i in self.interacoes)
        texto = (
            "Depois de entregar, você não poderá alterar a pesquisa até o professor aceitar ou devolver. "
            "O relatório fica disponível para ele."
        )
        if pendentes:
            texto = f"Ainda há {c.plural(pendentes, 'fonte', 'fontes')} sem verificar. " + texto
        if not c.perguntar(self.janela, "Entregar esta pesquisa ao professor?", texto, "Entregar para o professor"):
            return
        if self.janela.tentar(self.janela.pesquisas.entregar, self.pesquisa_id) is self.janela.FALHOU:
            return
        self.janela.abrir_pesquisa(self.pesquisa_id)
        self.janela.aviso("Pesquisa entregue. O professor vai revisar e você verá aqui se ele aceitar ou devolver.", "ok")
