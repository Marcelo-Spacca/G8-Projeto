"""Detalhe da pesquisa: interações (RF11, RF12), editar (RF08), concluir (RF10) e relatório (RF21)."""
from PySide6.QtWidgets import QDialog, QVBoxLayout

from services.fonte_service import contar_status
from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario


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

        self.botao_voltar = c.botao("‹ Minhas pesquisas", "link", self.janela.abrir_pesquisas)
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.titulo = c.rotulo(pesquisa.titulo, "titulo", selecionavel=True)
        self.selo = c.selo_status_pesquisa(pesquisa.status)
        self.corpo.addLayout(c.linha_horizontal(self.selo, None))
        self.corpo.addWidget(self.titulo)
        self.corpo.addWidget(c.rotulo(pesquisa.objetivo, "documento", selecionavel=True))
        if not aberta:
            self.corpo.addWidget(
                c.rotulo(
                    f"Concluída em {c.formatar_data(pesquisa.data_conclusao)}. Esta pesquisa foi entregue ao professor e não pode mais ser alterada.",
                    "mudo",
                )
            )

        self.botao_editar = c.botao("Editar título e objetivo", ao_clicar=self.editar)
        self.botao_relatorio = c.botao(
            "Ver relatório" if not aberta else "Ver prévia do relatório", ao_clicar=self.ver_relatorio
        )
        self.botao_concluir = c.botao("Concluir pesquisa", "primario", self.concluir)
        self.botao_excluir = c.botao("Excluir pesquisa", "perigo", self.excluir)
        acoes = [self.botao_relatorio]
        if aberta:
            acoes = [self.botao_editar, self.botao_relatorio, self.botao_concluir, None, self.botao_excluir]
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

    def excluir(self):  # RF09
        n = len(self.interacoes)
        extra = f" e {c.plural(n, 'interação registrada', 'interações registradas')}, com as fontes e os trechos," if n else ""
        texto = f"A pesquisa “{c.cortar(self.pesquisa.titulo, 60)}”{extra} serão apagadas. Isso não pode ser desfeito."
        if not c.perguntar(self.janela, "Excluir esta pesquisa?", texto, "Excluir", perigo=True):
            return
        if self.janela.tentar(self.janela.pesquisas.excluir, self.pesquisa_id) is self.janela.FALHOU:
            return
        self.janela.abrir_pesquisas()
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
        conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=16)
        conteudo.addLayout(esquerda, 1)
        conteudo.addWidget(direita)
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

    def ver_relatorio(self):
        self.janela.abrir_relatorio(self.pesquisa_id, "‹ Voltar para a pesquisa", lambda: self.janela.abrir_pesquisa(self.pesquisa_id))

    def concluir(self):
        pendentes = sum(contar_status(i.fontes)["nao_verificada"] for i in self.interacoes)
        texto = "Depois de concluir, a pesquisa não poderá mais ser alterada e o relatório ficará disponível para o professor."
        if pendentes:
            texto = f"Ainda há {c.plural(pendentes, 'fonte', 'fontes')} sem verificar. " + texto
        if not c.perguntar(self.janela, "Concluir esta pesquisa?", texto, "Concluir pesquisa"):
            return
        if self.janela.tentar(self.janela.pesquisas.concluir, self.pesquisa_id) is self.janela.FALHOU:
            return
        self.janela.abrir_relatorio(self.pesquisa_id, "‹ Voltar para a pesquisa", lambda: self.janela.abrir_pesquisa(self.pesquisa_id))
        self.janela.aviso("Pesquisa concluída. O relatório foi gerado e já está disponível para o professor.", "ok")
