"""Janelas de diálogo: formulário genérico e a janela de verificação de fonte.

Cada diálogo recebe uma 'acao' (função) que chama o service. Se o service recusar
(RegraViolada), a mensagem aparece dentro do diálogo e ele continua aberto para o usuário corrigir.
"""
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QLineEdit,
    QPlainTextEdit,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.componentes import botao, linha_horizontal, mensagem_de_erro, rotulo
from ui.tutoriais import TUTORIAIS


@dataclass
class Campo:
    chave: str
    rotulo: str
    tipo: str = "linha"  # linha, texto (várias linhas), senha ou caixa (marcar/desmarcar)
    dica: str = ""
    altura: int = 110


class _DialogoBase(QDialog):
    def __init__(self, parent, titulo, subtitulo=None, largura=540):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(largura)
        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(28, 24, 28, 22)
        self.raiz.setSpacing(8)
        self.raiz.addWidget(rotulo(titulo, "secao"))
        if subtitulo:
            self.raiz.addWidget(rotulo(subtitulo, "mudo"))
        self.raiz.addSpacing(4)

    def _rodape(self, rotulo_ok):
        self.erro = rotulo("", "erro")
        self.erro.hide()
        self.raiz.addWidget(self.erro)
        self.botao_cancelar = botao("Cancelar", ao_clicar=self.reject)
        self.botao_cancelar.setAutoDefault(False)
        self.botao_ok = botao(rotulo_ok, "primario", self.confirmar)
        self.botao_ok.setDefault(True)
        self.raiz.addSpacing(6)
        self.raiz.addLayout(linha_horizontal(None, self.botao_cancelar, self.botao_ok))

    def mostrar_erro(self, texto):
        self.erro.setText(texto)
        self.erro.show()

    def confirmar(self):
        """Chama a ação; se der certo fecha o diálogo, senão mostra o motivo e continua aberto."""
        self.erro.hide()
        try:
            self.acao(self.valores())
        except Exception as erro:  # RegraViolada ou erro inesperado: ambos viram texto na janela
            self.mostrar_erro(mensagem_de_erro(erro))
            return
        self.accept()


class DialogoFormulario(_DialogoBase):
    def __init__(self, parent, titulo, campos, acao, rotulo_ok="Salvar", subtitulo=None, valores=None):
        super().__init__(parent, titulo, subtitulo)
        self.acao = acao
        self.campos = {}
        for campo in campos:
            if campo.tipo == "caixa":
                entrada = QCheckBox(campo.rotulo)
                self.campos[campo.chave] = entrada
                self.raiz.addWidget(entrada)
                continue
            self.raiz.addWidget(rotulo(campo.rotulo, "campo"))
            if campo.tipo == "texto":
                entrada = QPlainTextEdit()
                entrada.setFixedHeight(campo.altura)
                entrada.setTabChangesFocus(True)
            else:
                entrada = QLineEdit()
                if campo.tipo == "senha":
                    entrada.setEchoMode(QLineEdit.Password)
                entrada.returnPressed.connect(self.confirmar)
            entrada.setPlaceholderText(campo.dica)
            self.campos[campo.chave] = entrada
            self.raiz.addWidget(entrada)
        self._rodape(rotulo_ok)
        if valores:
            self.definir(**valores)
        if self.campos:
            next(iter(self.campos.values())).setFocus()

    def definir(self, **valores):
        for chave, texto in valores.items():
            entrada = self.campos[chave]
            if isinstance(entrada, QCheckBox):
                entrada.setChecked(bool(texto))
            elif isinstance(entrada, QPlainTextEdit):
                entrada.setPlainText(texto or "")
            else:
                entrada.setText(texto or "")

    def valores(self):
        def valor(e):
            if isinstance(e, QCheckBox):
                return e.isChecked()
            return e.toPlainText() if isinstance(e, QPlainTextEdit) else e.text()

        return {chave: valor(e) for chave, e in self.campos.items()}


class DialogoConvidar(_DialogoBase):
    """O aluno marca os colegas da turma que quer convidar para o grupo."""

    def __init__(self, parent, grupo, candidatos, acao):
        super().__init__(
            parent,
            f"Convidar para o grupo “{grupo.nome}”",
            "Marque os colegas da turma que vão fazer esta pesquisa com você. "
            "A pesquisa do grupo é criada quando o primeiro deles aceitar o convite.",
        )
        self.acao = acao
        self.caixas = {}
        for aluno in candidatos:
            caixa = QCheckBox(aluno.nome)
            self.caixas[aluno.id] = caixa
            self.raiz.addWidget(caixa)
        self._rodape("Enviar convites")

    def marcar(self, *alunos_ids):
        for aluno_id in alunos_ids:
            self.caixas[aluno_id].setChecked(True)

    def valores(self):
        return {"alunos_ids": [i for i, caixa in self.caixas.items() if caixa.isChecked()]}


class DialogoEscolherAluno(_DialogoBase):
    """O professor escolhe um aluno da turma para colocar no grupo."""

    def __init__(self, parent, grupo, candidatos, acao):
        super().__init__(
            parent,
            f"Atribuir aluno ao grupo “{grupo.nome}”",
            "Escolha o aluno da turma que passa a fazer parte deste grupo.",
        )
        self.acao = acao
        self.combo = QComboBox()
        for aluno in candidatos:
            self.combo.addItem(aluno.nome, aluno.id)
        self.raiz.addWidget(self.combo)
        self._rodape("Atribuir ao grupo")

    def escolher(self, aluno_id):
        self.combo.setCurrentIndex(self.combo.findData(aluno_id))

    def valores(self):
        return {"aluno_id": self.combo.currentData()}


class DialogoConvites(_DialogoBase):
    """Convites de grupo que o aluno recebeu na turma: aceitar ou recusar cada um."""

    def __init__(self, parent, convites, responder):
        super().__init__(
            parent,
            "Convites para grupos",
            "Ao aceitar, você entra no grupo e passa a fazer a pesquisa dele junto com os outros integrantes.",
            largura=580,
        )
        self.responder = responder  # função(convite_id, aceitar); levanta RegraViolada se recusar
        self.respostas = []         # (nome do grupo, aceitou?) de cada convite respondido aqui
        self.itens = []
        self.erro = rotulo("", "erro")
        self.erro.hide()
        self.raiz.addWidget(self.erro)
        self.vazio = rotulo("Nenhum convite pendente.", "vazio")
        self.raiz.addWidget(self.vazio)
        for convite in convites:
            self.itens.append(self._item(convite))
        self.vazio.setVisible(not self.itens)
        self.botao_fechar = botao("Fechar", "primario", self.accept)
        self.botao_ok = self.botao_fechar  # mesmo nome dos outros diálogos (os testes clicam nele)
        self.raiz.addSpacing(6)
        self.raiz.addLayout(linha_horizontal(None, self.botao_fechar))

    def _item(self, convite):
        quadro = QFrame()
        quadro.setProperty("papel", "painel")
        v = QVBoxLayout(quadro)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)
        quadro.convite_id = convite.id
        quadro.grupo_nome = convite.grupo.nome
        quem = convite.convidado_por.nome if convite.convidado_por else "Um colega"
        v.addWidget(rotulo(f"Grupo {convite.grupo.nome}", "item"))
        v.addWidget(rotulo(f"{quem} convidou você para a pesquisa “{convite.grupo.titulo}”.", "mudo"))
        integrantes = ", ".join(a.nome for a in convite.grupo.alunos)
        v.addWidget(rotulo(f"Integrantes até agora: {integrantes}", "dica"))
        quadro.botao_aceitar = botao("Aceitar", "primario", lambda q=quadro: self._responder(q, True))
        quadro.botao_recusar = botao("Recusar", ao_clicar=lambda q=quadro: self._responder(q, False))
        v.addLayout(linha_horizontal(None, quadro.botao_recusar, quadro.botao_aceitar))
        self.raiz.insertWidget(self.raiz.indexOf(self.vazio), quadro)
        return quadro

    def _responder(self, quadro, aceitar):
        self.erro.hide()
        try:
            self.responder(quadro.convite_id, aceitar)
        except Exception as erro:
            self.mostrar_erro(mensagem_de_erro(erro))
            return
        self.respostas.append((quadro.grupo_nome, aceitar))
        self.itens.remove(quadro)
        quadro.setParent(None)
        quadro.deleteLater()
        self.vazio.setVisible(not self.itens)


class DialogoTutorial(QDialog):
    """Janela de ajuda de uma tela. 'chave' é uma das chaves de ui.tutoriais.TUTORIAIS."""

    def __init__(self, parent, chave):
        super().__init__(parent)
        tutorial = TUTORIAIS[chave]
        self.chave = chave
        self.setWindowTitle("Tutorial")
        self.setModal(True)
        self.setMinimumSize(560, 460)
        self.resize(640, 600)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(28, 24, 28, 22)
        raiz.setSpacing(10)
        self.titulo = rotulo(tutorial["titulo"], "secao")
        raiz.addWidget(self.titulo)

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        conteudo = QWidget()
        conteudo.setObjectName("tutorial")
        v = QVBoxLayout(conteudo)
        v.setContentsMargins(0, 0, 12, 0)
        v.setSpacing(8)
        v.addWidget(rotulo(tutorial["abertura"], "documento"))
        self.secoes = []
        for cabecalho, topicos in tutorial["secoes"]:
            v.addSpacing(8)
            v.addWidget(rotulo(cabecalho, "item"))
            for topico in topicos:
                linha = rotulo(f"•  {topico}", "documento")
                self.secoes.append(linha)
                v.addWidget(linha)
        v.addStretch(1)
        rolagem.setWidget(conteudo)
        raiz.addWidget(rolagem, 1)

        self.botao_fechar = botao("Entendi", "primario", self.accept)
        self.botao_fechar.setDefault(True)
        raiz.addLayout(linha_horizontal(None, self.botao_fechar))

    def texto(self):
        """Todo o texto do tutorial (útil para conferir nos testes)."""
        partes = [self.titulo.text()]
        for filho in self.findChildren(type(self.titulo)):
            partes.append(filho.text())
        return "\n".join(partes)


class DialogoVerificacao(_DialogoBase):
    """RF17/RF18/RF26: o aluno confere a fonte, anota o que encontrou e liga o trecho do texto."""

    OPCOES = (
        ("verificada", "Verificada: existe e confirma o que a IA disse"),
        ("incorreta", "Incorreta ou inventada"),
        ("nao_verificada", "Ainda não verificada"),
    )

    def __init__(self, parent, fonte, acao, professor=False):
        super().__init__(
            parent,
            "Julgar fonte" if professor else "Verificar fonte",
            "Confira a fonte e registre o seu julgamento. O aluno lê a sua anotação."
            if professor
            else "Confira a fonte por conta própria, fora da IA.",
            largura=600,
        )
        self.professor = professor
        self.acao = acao
        self.raiz.addWidget(rotulo(fonte.referencia, "item", selecionavel=True))
        if fonte.link:
            self.raiz.addWidget(rotulo(fonte.link, "mudo", selecionavel=True))
        self.raiz.addSpacing(6)
        self.raiz.addWidget(rotulo("Qual é o seu julgamento?" if professor else "Qual é o resultado da sua conferência?", "campo"))

        self.opcoes = {}
        grupo = QButtonGroup(self)
        for chave, texto in self.OPCOES:
            radio = QRadioButton(texto)
            grupo.addButton(radio)
            self.opcoes[chave] = radio
            self.raiz.addWidget(radio)
        self.raiz.addSpacing(4)
        self.rotulo_anotacao = rotulo("O que você encontrou (opcional)", "campo")
        self.raiz.addWidget(self.rotulo_anotacao)
        self.anotacao = QPlainTextEdit()
        self.anotacao.setFixedHeight(80)
        self.anotacao.setTabChangesFocus(True)
        self.anotacao.setPlaceholderText("Ex.: o artigo existe, mas o ano é 2021 e não 2023.")
        self.anotacao.setPlainText(fonte.anotacao_correcao or "")
        if professor:
            self.anotacao.setPlaceholderText("Ex.: não encontrei este artigo em nenhuma base.")
        self.raiz.addWidget(self.anotacao)

        self.grupo_trecho = QWidget()
        interno = QVBoxLayout(self.grupo_trecho)
        interno.setContentsMargins(0, 0, 0, 0)
        interno.setSpacing(8)
        ja_ligados = len(fonte.trechos)
        titulo_trecho = "Em que trecho do seu texto você usou esta fonte? (opcional)"
        if ja_ligados:
            titulo_trecho = f"Ligar outro trecho do seu texto (opcional). Já há {ja_ligados} ligado(s)."
        interno.addWidget(rotulo(titulo_trecho, "campo"))
        self.trecho = QPlainTextEdit()
        self.trecho.setFixedHeight(80)
        self.trecho.setTabChangesFocus(True)
        self.trecho.setPlaceholderText("Cole aqui a frase ou o parágrafo do seu trabalho.")
        interno.addWidget(self.trecho)
        self.localizacao = QLineEdit()
        self.localizacao.setPlaceholderText("Onde fica: parágrafo ou linha (opcional)")
        interno.addWidget(self.localizacao)
        if not professor:  # o trecho é do texto do aluno: só ele liga
            self.raiz.addWidget(self.grupo_trecho)
        else:
            self.grupo_trecho.hide()

        self.aviso_trechos = rotulo(
            f"Os {ja_ligados} trechos que o aluno ligou a esta fonte serão removidos."
            if ja_ligados != 1 and professor
            else "O trecho que o aluno ligou a esta fonte será removido."
            if professor
            else f"Os {ja_ligados} trechos ligados a esta fonte serão removidos."
            if ja_ligados != 1
            else "O trecho ligado a esta fonte será removido.",
            "erro",
        )
        self.aviso_trechos.hide()
        self._ja_ligados = ja_ligados
        self.raiz.addWidget(self.aviso_trechos)

        self._rodape("Salvar verificação")
        # só agora, com todos os campos criados, as opções passam a reagir à troca de status
        self.opcoes[fonte.status].setChecked(True)
        for radio in self.opcoes.values():
            radio.toggled.connect(self._atualizar)
        self._atualizar()

    def resultado(self):
        return next(chave for chave, radio in self.opcoes.items() if radio.isChecked())

    def _atualizar(self, *_):
        verificada = self.resultado() == "verificada"
        self.grupo_trecho.setEnabled(verificada)
        if self.resultado() == "incorreta":
            texto = "Anotação de correção: o que está errado nesta fonte? (opcional)"
        else:
            texto = "Sua anotação para o aluno (opcional)" if self.professor else "O que você encontrou (opcional)"
        self.rotulo_anotacao.setText(texto)
        self.aviso_trechos.setVisible(not verificada and self._ja_ligados > 0)

    def valores(self):
        return {
            "resultado": self.resultado(),
            "anotacao": self.anotacao.toPlainText(),
            "trecho": self.trecho.toPlainText() if self.resultado() == "verificada" and not self.professor else "",
            "localizacao": self.localizacao.text(),
        }
