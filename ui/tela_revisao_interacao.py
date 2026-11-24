"""Interação de um aluno vista pelo professor: julgar as fontes, comentar e confirmar."""
from PySide6.QtWidgets import QDialog

from ui import cartao_fonte
from ui import componentes as c
from ui.dialogos import Campo, DialogoFormulario, DialogoTutorial, DialogoVerificacao


class TelaRevisaoInteracao(c.TelaBase):
    interacao_id = None

    def carregar(self, interacao_id):
        interacao = self.janela.revisoes.obter_interacao(interacao_id)
        pesquisa = self.janela.revisoes.obter_pesquisa(interacao.pesquisa_id)
        self.interacao_id = interacao.id
        self.interacao = interacao
        self.pesquisa = pesquisa
        em_revisao = pesquisa.status == "entregue"
        pode_julgar = em_revisao and not interacao.confirmada
        fontes = sorted(interacao.fontes, key=lambda f: f.id)
        self.fontes = fontes
        self.reiniciar()

        self.botao_voltar = c.botao(f"‹ {c.cortar(pesquisa.titulo, 50)}", "link", lambda: self.janela.abrir_revisao(pesquisa.id))
        self.corpo.addLayout(c.linha_horizontal(self.botao_voltar, None))
        self.botao_tutorial = c.botao_tutorial(self.tutorial)
        self.titulo = c.rotulo(f"Interação com {interacao.ferramenta_ia}", "titulo", selecionavel=True)
        self.corpo.addLayout(c.linha_horizontal(self.titulo, self.botao_tutorial))
        chips = []
        if interacao.confirmada:
            chips.append(c.selo("Confirmada", "verificada"))
        self.corpo.addLayout(
            c.linha_horizontal(
                c.rotulo(f"{c.autor_da_pesquisa(pesquisa) if pesquisa.de_grupo else 'Aluno: ' + pesquisa.aluno.nome}  ·  registrada em {c.formatar_data(interacao.data_registro)}", "mudo", quebra=False),
                *chips,
                None,
            )
        )
        self.aviso_estado = None
        if pesquisa.status == "em_andamento":
            self.aviso_estado = c.rotulo(
                "A pesquisa ainda está com o aluno: você acompanha, mas só pode julgar e comentar depois que ele entregar.", "mudo"
            )
        elif pesquisa.status == "concluida":
            self.aviso_estado = c.rotulo("Pesquisa concluída: nada mais pode ser alterado.", "mudo")
        if self.aviso_estado is not None:
            self.corpo.addWidget(self.aviso_estado)

        self.botao_confirmar = c.botao("Confirmar interação", "primario", self.confirmar)
        self.botao_reabrir = c.botao("Reabrir interação", ao_clicar=self.reabrir)
        if em_revisao:
            self.corpo.addLayout(c.linha_horizontal(self.botao_reabrir if interacao.confirmada else self.botao_confirmar, None))

        self.painel_pergunta = c.painel_texto("Pergunta", interacao.pergunta)
        self.painel_resposta = c.painel_texto("Resposta da IA", interacao.resposta)
        self.corpo.addWidget(self.painel_pergunta)
        self.corpo.addWidget(self.painel_resposta)
        self.corpo.addSpacing(8)

        # comentário do professor
        self.botao_comentar = c.botao(
            "Editar comentário" if interacao.comentario_professor else "Comentar", ao_clicar=self.comentar
        )
        cabecalho = [c.rotulo("Seu comentário", "secao", quebra=False), None]
        if em_revisao:
            cabecalho.append(self.botao_comentar)
        self.corpo.addLayout(c.linha_horizontal(*cabecalho))
        self.comentario = None
        if interacao.comentario_professor:
            self.comentario = c.recado(
                f"Comentário · {c.formatar_data(interacao.data_comentario)}",
                interacao.comentario_professor,
                "comentario",
            )
            self.corpo.addWidget(self.comentario)
        else:
            self.corpo.addWidget(c.rotulo("Nenhum comentário. O aluno lê o que você escrever aqui, mas não responde." if em_revisao else "Nenhum comentário nesta interação.", "dica"))
        self.corpo.addSpacing(8)

        self.corpo.addWidget(c.rotulo("Fontes citadas pela IA", "secao", quebra=False))
        if fontes:
            self.corpo.addWidget(c.rotulo(c.resumo_fontes(self._contagem(fontes)), "mudo"))
        self.cartoes = []
        if not fontes:
            self.corpo.addWidget(self.vazio("O aluno não cadastrou fontes nesta interação."))
        for fonte in fontes:
            cartao = cartao_fonte.montar(fonte, "professor")
            cartao.botao_julgar = c.botao(
                "Julgar fonte" if fonte.status == "nao_verificada" else "Alterar julgamento",
                "primario" if fonte.status == "nao_verificada" else "secundario",
                lambda f=fonte: self.julgar(f),
            )
            if pode_julgar:
                cartao.v.addSpacing(2)
                cartao.v.addLayout(c.linha_horizontal(cartao.botao_julgar, None))
            self.cartoes.append(cartao)
            self.corpo.addWidget(cartao)
        self.corpo.addStretch(1)

    @staticmethod
    def _contagem(fontes):
        from services.fonte_service import contar_status

        return contar_status(fontes)

    # ------------------------------------------------------------ ações
    def tutorial(self):
        c.abrir(DialogoTutorial(self.janela, "prof_interacao"))

    def _recarregar(self, mensagem):
        self.janela.abrir_revisao_interacao(self.interacao_id)
        self.janela.aviso(mensagem, "ok")

    def julgar(self, fonte):
        dialogo = DialogoVerificacao(
            self.janela,
            fonte,
            lambda v: self.janela.revisoes.julgar_fonte(fonte.id, v["resultado"], v["anotacao"]),
            professor=True,
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self._recarregar("Julgamento salvo. O aluno verá a sua decisão.")

    def comentar(self):
        dialogo = DialogoFormulario(
            self.janela,
            "Comentar a interação",
            [Campo("comentario", "Comentário para o aluno", "texto", altura=130)],
            lambda v: self.janela.revisoes.comentar_interacao(self.interacao_id, v["comentario"]),
            subtitulo="O aluno lê este comentário, mas não pode responder. Deixe em branco para apagar.",
            valores={"comentario": self.interacao.comentario_professor or ""},
            rotulo_ok="Salvar comentário",
        )
        if c.abrir(dialogo) == QDialog.Accepted:
            self._recarregar("Comentário salvo.")

    def confirmar(self):
        texto = "O aluno não poderá mais alterar esta interação nem as fontes dela. Se precisar de ajustes, ele cria uma nova interação."
        if not c.perguntar(self.janela, "Confirmar esta interação?", texto, "Confirmar interação"):
            return
        if self.janela.tentar(self.janela.revisoes.confirmar_interacao, self.interacao_id) is self.janela.FALHOU:
            return
        self._recarregar("Interação confirmada e fechada para o aluno.")

    def reabrir(self):
        if self.janela.tentar(self.janela.revisoes.reabrir_interacao, self.interacao_id) is self.janela.FALHOU:
            return
        self._recarregar("Interação reaberta.")
