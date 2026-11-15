"""Detalhe da interação: texto, editar (RF13), excluir (RF14) e as fontes (RF15 a RF19, RF26, RF27)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QVBoxLayout

from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario, DialogoVerificacao


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
        editavel = pesquisa.status == "em_andamento"
        self.reiniciar()

        self.botao_voltar = c.botao(f"‹ {c.cortar(pesquisa.titulo, 50)}", "link", lambda: self.janela.abrir_pesquisa(pesquisa.id))
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))

        self.botao_editar = c.botao("Editar", ao_clicar=self.editar)
        self.botao_excluir = c.botao("Excluir", "perigo", self.excluir)
        acoes = ([self.botao_editar, self.botao_excluir] if editavel else [])
        self.titulo = c.rotulo(f"Interação com {interacao.ferramenta_ia}", "titulo", selecionavel=True)
        self.corpo.addLayout(c.linha_horizontal(self.titulo, *acoes))
        self.corpo.addWidget(c.rotulo(f"Registrada em {c.formatar_data(interacao.data_registro)}", "mudo"))
        if not editavel:
            self.corpo.addWidget(c.rotulo("A pesquisa foi concluída e entregue ao professor: esta interação e suas fontes não podem mais ser alteradas.", "mudo"))

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
        cartao = QFrame()
        cartao.setProperty("papel", "fonte")
        cartao.setProperty("status", fonte.status)
        cartao.fonte_id = fonte.id
        v = QVBoxLayout(cartao)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(6)
        selo = c.selo_status_fonte(fonte.status)
        referencia = c.rotulo(fonte.referencia, "item", selecionavel=True)
        v.addLayout(c.linha_horizontal(referencia, selo))
        cartao.selo = selo
        cartao.referencia = referencia
        if fonte.link:
            link = QLabel()
            link.setWordWrap(True)
            if fonte.link.lower().startswith(("http://", "https://")):
                from html import escape

                link.setText(f'<a href="{escape(fonte.link, quote=True)}">{escape(fonte.link)}</a>')
                link.setOpenExternalLinks(True)
            else:
                link.setText(fonte.link)
                link.setTextInteractionFlags(Qt.TextSelectableByMouse)
            v.addWidget(link)
            cartao.link = link
        if fonte.anotacao_correcao:
            v.addWidget(c.rotulo(f"Anotação: {fonte.anotacao_correcao}", "mudo", selecionavel=True))
        cartao.trechos = []
        trechos = sorted(fonte.trechos, key=lambda t: t.id)
        if trechos:
            v.addWidget(c.rotulo("Usada no seu texto em:", "dica"))
        if not trechos:
            sem = "Fonte descartada: sem trecho no seu texto." if fonte.status == "incorreta" else "Ainda sem trecho vinculado."
            v.addWidget(c.rotulo(sem, "dica"))
        for t in trechos:
            onde = f"  ({t.localizacao})" if t.localizacao else ""
            texto = c.rotulo(f"“{t.trecho_citado}”{onde}", "trecho", selecionavel=True)
            cartao.trechos.append(texto)
            v.addWidget(texto)
        cartao.botao_verificar = c.botao(
            "Verificar" if fonte.status == "nao_verificada" else "Alterar verificação",
            "primario" if fonte.status == "nao_verificada" else "secundario",
            lambda f=fonte: self.verificar(f),
        )
        cartao.botao_trecho = c.botao("Ligar outro trecho", ao_clicar=lambda f=fonte: self.ligar_trecho(f))
        if editavel:
            acoes = [cartao.botao_verificar]
            if fonte.status == "verificada":
                acoes.append(cartao.botao_trecho)
            v.addSpacing(2)
            v.addLayout(c.linha_horizontal(*acoes, None))
        return cartao

    # ------------------------------------------------------------ ações
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
