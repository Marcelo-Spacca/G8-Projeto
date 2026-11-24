"""Detalhe da interação: texto, editar (RF13), excluir (RF14) e as fontes (RF15 a RF19, RF26, RF27)."""
from PySide6.QtWidgets import QDialog, QFrame, QVBoxLayout

from ui import cartao_fonte
from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario, DialogoTutorial, DialogoVerificacao


class TelaInteracao(c.TelaBase):
    interacao_id = None

    def carregar(self, interacao_id):
        interacao = self.janela.interacoes.obter(interacao_id)
        pesquisa = self.janela.pesquisas.obter(interacao.pesquisa_id)
        fontes = self.janela.fontes.listar(interacao_id)
        self.interacao_id = interacao.id
        self.interacao = interacao
        self.pesquisa = pesquisa
        self.fontes = fontes
        com_o_aluno = pesquisa.status == "em_andamento"
        # interação confirmada pelo professor está fechada: só a pesquisa devolvida pode ter outras abertas
        editavel = com_o_aluno and not interacao.confirmada
        self.reiniciar()

        self.botao_voltar = c.botao(f"‹ {c.cortar(pesquisa.titulo, 50)}", "link", lambda: self.janela.abrir_pesquisa(pesquisa.id))
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))

        self.botao_editar = c.botao("Editar", ao_clicar=self.editar)
        self.botao_excluir = c.botao("Excluir", "perigo", self.excluir)
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        acoes = [self.botao_editar, self.botao_tutorial, self.botao_excluir] if editavel else [self.botao_tutorial]
        self.titulo = c.rotulo(f"Interação com {interacao.ferramenta_ia}", "titulo", selecionavel=True)
        self.corpo.addLayout(c.linha_horizontal(self.titulo, *acoes))
        chips = []
        if interacao.confirmada:
            chips.append(c.selo("Confirmada pelo professor", "verificada"))
        self.corpo.addLayout(
            c.linha_horizontal(c.rotulo(f"Registrada em {c.formatar_data(interacao.data_registro)}", "mudo", quebra=False), *chips, None)
        )
        self.aviso_estado = None
        if not com_o_aluno:
            self.aviso_estado = c.rotulo(
                "A pesquisa está com o professor ou já foi concluída: esta interação e suas fontes não podem ser alteradas.", "mudo"
            )
        elif interacao.confirmada:
            self.aviso_estado = c.rotulo(
                "O professor confirmou esta interação e ela não pode mais ser alterada. Se precisar ajustar algo, crie uma nova interação na pesquisa.",
                "mudo",
            )
        if self.aviso_estado is not None:
            self.corpo.addWidget(self.aviso_estado)
        self.comentario = None
        if interacao.comentario_professor:
            self.comentario = c.recado(
                f"Comentário do professor · {c.formatar_data(interacao.data_comentario)}",
                interacao.comentario_professor,
                "comentario",
            )
            self.corpo.addWidget(self.comentario)

        self.painel_pergunta = self._painel("Pergunta", interacao.pergunta)
        self.painel_resposta = self._painel("Resposta da IA", interacao.resposta)
        self.corpo.addWidget(self.painel_pergunta)
        self.corpo.addWidget(self.painel_resposta)
        self.corpo.addSpacing(8)

        self.botao_adicionar_fonte = c.botao("+ Adicionar fonte", "primario", self.adicionar_fonte)
        cabecalho = [c.rotulo("Fontes citadas pela IA", "secao", quebra=False), None]
        if editavel:
            cabecalho.append(self.botao_adicionar_fonte)
        self.corpo.addLayout(c.linha_horizontal(*cabecalho))
        if fontes:
            self.corpo.addWidget(c.rotulo(c.resumo_fontes(self._contagem(fontes)), "mudo"))

        self.cartoes = []
        if not fontes:
            self.corpo.addWidget(self.vazio("Nenhuma fonte cadastrada. Se a IA citou livros, artigos ou sites, cadastre cada um para poder conferi-los depois." if editavel else "Nenhuma fonte foi cadastrada nesta interação."))
        for fonte in fontes:
            cartao = self._cartao_fonte(fonte, editavel)
            self.cartoes.append(cartao)
            self.corpo.addWidget(cartao)
        self.corpo.addStretch(1)

    @staticmethod
    def _contagem(fontes):
        from services.fonte_service import contar_status

        return contar_status(fontes)

    def _painel(self, titulo, texto):
        painel = QFrame()
        painel.setProperty("papel", "painel")
        v = QVBoxLayout(painel)
        v.setContentsMargins(20, 14, 20, 16)
        v.setSpacing(6)
        v.addWidget(c.rotulo(titulo, "campo"))
        corpo = c.rotulo(texto, "documento", selecionavel=True)
        painel.texto = corpo
        v.addWidget(corpo)
        return painel

    def _cartao_fonte(self, fonte, editavel):
        cartao = cartao_fonte.montar(fonte, "aluno")
        cartao.botao_verificar = c.botao(
            "Verificar" if fonte.status == "nao_verificada" else "Alterar verificação",
            "primario" if fonte.status == "nao_verificada" else "secundario",
            lambda f=fonte: self.verificar(f),
        )
        cartao.botao_trecho = c.botao("Ligar outro trecho", ao_clicar=lambda f=fonte: self.ligar_trecho(f))
        cartao.botao_editar = c.botao("Editar fonte", ao_clicar=lambda f=fonte: self.editar_fonte(f))
        if editavel:
            acoes = [cartao.botao_verificar]
            if fonte.status == "verificada":
                acoes.append(cartao.botao_trecho)
            acoes.append(cartao.botao_editar)
            cartao.v.addSpacing(2)
            cartao.v.addLayout(c.linha_horizontal(*acoes, None))
        return cartao

    # ------------------------------------------------------------ ações
    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "aluno_interacao"))

    def editar(self):
        i = self.interacao
        dialogo = DialogoFormulario(
            self.janela,
            "Editar interação",
            [
                Campo("ferramenta", "Ferramenta de IA usada"),
                Campo("pergunta", "Pergunta feita", "texto", altura=100),
                Campo("resposta", "Resposta obtida", "texto", altura=140),
            ],
            lambda v: self.janela.interacoes.editar(i.id, v["ferramenta"], v["pergunta"], v["resposta"]),
            subtitulo="As fontes cadastradas continuam as mesmas.",
            valores={"ferramenta": i.ferramenta_ia, "pergunta": i.pergunta, "resposta": i.resposta},
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_interacao(i.id)
            self.janela.aviso("Interação atualizada.", "ok")

    def excluir(self):
        n = len(self.fontes)
        extra = f" e {c.plural(n, 'fonte cadastrada', 'fontes cadastradas')}, com os trechos ligados," if n else ""
        texto = f"A pergunta, a resposta{extra} serão apagadas. Isso não pode ser desfeito."
        if not c.perguntar(self.janela, "Excluir esta interação?", texto, "Excluir", perigo=True):
            return
        if self.janela.tentar(self.janela.interacoes.excluir, self.interacao_id) is self.janela.FALHOU:
            return
        self.janela.abrir_pesquisa(self.pesquisa.id)
        self.janela.aviso("Interação excluída.", "ok")

    def adicionar_fonte(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Adicionar fonte",
            [
                Campo("referencia", "Referência citada pela IA", dica="Ex.: SILVA, J. A educação na era da IA. 2023."),
                Campo("link", "Link (opcional)", dica="https://"),
            ],
            lambda v: self.janela.fontes.adicionar(self.interacao_id, v["referencia"], v["link"]),
            subtitulo="A fonte entra como “não verificada” até você conferi-la.",
            rotulo_ok="Adicionar fonte",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_interacao(self.interacao_id)
            self.janela.aviso("Fonte adicionada como não verificada.", "ok")

    def editar_fonte(self, fonte):
        julgada = fonte.status != "nao_verificada"
        aviso = (
            "Atenção: esta fonte já foi conferida. Se você mudar a referência ou o link, ela volta a "
            "“não verificada” e os trechos ligados a ela são removidos, para você conferir de novo."
            if julgada
            else "Corrija a referência ou o link. A fonte continua “não verificada”."
        )
        dialogo = DialogoFormulario(
            self.janela,
            "Editar fonte",
            [
                Campo("referencia", "Referência citada pela IA", "texto", altura=80),
                Campo("link", "Link (opcional)", dica="https://"),
            ],
            self._salvar_edicao_da_fonte(fonte),
            subtitulo=aviso,
            rotulo_ok="Salvar fonte",
            valores={"referencia": fonte.referencia, "link": fonte.link or ""},
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_interacao(self.interacao_id)
            if julgada and self._fonte_editada.status == "nao_verificada":
                self.janela.aviso("Fonte atualizada. Como o conteúdo mudou, ela voltou a “não verificada”.", "ok")
            else:
                self.janela.aviso("Fonte atualizada.", "ok")

    def _salvar_edicao_da_fonte(self, fonte):
        def salvar(valores):
            self._fonte_editada = self.janela.fontes.editar(fonte.id, valores["referencia"], valores["link"])

        return salvar

    def verificar(self, fonte):
        dialogo = DialogoVerificacao(
            self.janela,
            fonte,
            lambda v: self.janela.fontes.verificar(fonte.id, v["resultado"], v["anotacao"], v["trecho"], v["localizacao"]),
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_interacao(self.interacao_id)
            self.janela.aviso("Verificação salva.", "ok")

    def ligar_trecho(self, fonte):
        dialogo = DialogoFormulario(
            self.janela,
            "Ligar trecho do seu texto",
            [
                Campo("trecho", "Trecho do seu texto em que usou esta fonte", "texto", altura=110),
                Campo("localizacao", "Onde fica (opcional)", dica="Ex.: parágrafo 3"),
            ],
            lambda v: self.janela.fontes.ligar_trecho(fonte.id, v["trecho"], v["localizacao"]),
            subtitulo=fonte.referencia,
            rotulo_ok="Ligar trecho",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self.janela.abrir_interacao(self.interacao_id)
            self.janela.aviso("Trecho ligado à fonte.", "ok")
