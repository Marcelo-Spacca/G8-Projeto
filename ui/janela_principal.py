"""Janela principal: barra superior, avisos e a troca entre as telas.

Também é aqui que cada perfil fica no seu lugar (RF03): uma tela de aluno nunca abre para o
professor e a do professor nunca abre para o aluno, mesmo que algum código tente chamá-la.
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from services.fonte_service import FonteService
from services.grupo_service import GrupoService
from services.interacao_service import InteracaoService
from services.pesquisa_service import PesquisaService
from services.relatorio_service import RelatorioService
from services.revisao_service import RevisaoService
from services.sessao import sessao
from services.turma_service import TurmaService
from services.usuario_service import UsuarioService
from ui import componentes as c
from ui.tela_acesso import TelaAcesso
from ui.tela_interacao import TelaInteracao
from ui.tela_pesquisa import TelaPesquisa
from ui.tela_pesquisas import TelaPesquisas
from ui.tela_professor import TelaProfessor
from ui.tela_turma_professor import TelaTurmaProfessor
from ui.tela_turmas import TelaTurmas
from ui.tela_turmas_professor import TelaTurmasProfessor
from ui.tela_revisao import TelaRevisao
from ui.tela_revisao_interacao import TelaRevisaoInteracao
from ui.tela_relatorio import TelaRelatorio

NOME_DO_PERFIL = {"aluno": "Aluno", "professor": "Professor"}


class JanelaPrincipal(QMainWindow):
    FALHOU = object()  # devolvido por 'tentar' quando um service recusa a ação

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro verificável do uso de IA")
        self.resize(1120, 780)
        self.setMinimumSize(860, 560)

        self.usuarios = UsuarioService()
        self.pesquisas = PesquisaService()
        self.interacoes = InteracaoService()
        self.fontes = FonteService()
        self.relatorios = RelatorioService()
        self.revisoes = RevisaoService()
        self.turmas = TurmaService()
        self.grupos = GrupoService()

        central = QWidget()
        central.setObjectName("fundo")
        self.setCentralWidget(central)
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._montar_barra())
        self.faixa_aviso = QLabel()
        self.faixa_aviso.setObjectName("aviso")
        self.faixa_aviso.setWordWrap(True)
        self.faixa_aviso.hide()
        raiz.addWidget(self.faixa_aviso)
        self.pilha = QStackedWidget()
        self.pilha.setObjectName("pilha")
        raiz.addWidget(self.pilha, 1)

        self._timer_aviso = QTimer(self)
        self._timer_aviso.setSingleShot(True)
        self._timer_aviso.timeout.connect(self.limpar_aviso)

        self.tela_acesso = TelaAcesso(self)
        self.tela_turmas = TelaTurmas(self)
        self.tela_pesquisas = TelaPesquisas(self)
        self.tela_pesquisa = TelaPesquisa(self)
        self.tela_interacao = TelaInteracao(self)
        self.tela_relatorio = TelaRelatorio(self)
        self.tela_turmas_professor = TelaTurmasProfessor(self)
        self.tela_turma_professor = TelaTurmaProfessor(self)
        self.tela_professor = TelaProfessor(self)
        self.tela_revisao = TelaRevisao(self)
        self.tela_revisao_interacao = TelaRevisaoInteracao(self)
        for tela in (
            self.tela_acesso, self.tela_turmas, self.tela_pesquisas, self.tela_pesquisa,
            self.tela_interacao, self.tela_relatorio, self.tela_turmas_professor,
            self.tela_turma_professor, self.tela_professor,
            self.tela_revisao, self.tela_revisao_interacao,
        ):
            self.pilha.addWidget(tela)
        # Quem pode abrir cada tela. O relatório é aberto pelos dois; o service decide o que cada um vê.
        self._perfil_da_tela = {
            self.tela_turmas: "aluno",
            self.tela_pesquisas: "aluno",
            self.tela_pesquisa: "aluno",
            self.tela_interacao: "aluno",
            self.tela_turmas_professor: "professor",
            self.tela_turma_professor: "professor",
            self.tela_professor: "professor",
            self.tela_revisao: "professor",
            self.tela_revisao_interacao: "professor",
        }
        self.ir_para_acesso()

    # ------------------------------------------------------------ barra
    def _montar_barra(self):
        from PySide6.QtWidgets import QFrame, QHBoxLayout

        barra = QFrame()
        barra.setObjectName("barra")
        barra.setFixedHeight(54)
        h = QHBoxLayout(barra)
        h.setContentsMargins(24, 0, 20, 0)
        h.setSpacing(14)
        marca = QLabel("Registro verificável do uso de IA")
        marca.setObjectName("marca")
        self.rotulo_usuario = QLabel("")
        self.rotulo_usuario.setObjectName("quem")
        self.botao_sair = c.botao("Sair", ao_clicar=self.sair)
        h.addWidget(marca)
        h.addStretch(1)
        h.addWidget(self.rotulo_usuario)
        h.addWidget(self.botao_sair)
        return barra

    def _atualizar_barra(self):
        if sessao.logado:
            u = sessao.usuario
            self.rotulo_usuario.setText(f"{u.nome} · {NOME_DO_PERFIL[u.tipo]}")
        self.rotulo_usuario.setVisible(sessao.logado)
        self.botao_sair.setVisible(sessao.logado)

    # ------------------------------------------------------------ avisos
    def aviso(self, texto, tipo="info"):
        """Mostra uma faixa no topo da tela. tipo: ok, erro ou info."""
        self.faixa_aviso.setProperty("tipo", tipo)
        self.faixa_aviso.style().unpolish(self.faixa_aviso)
        self.faixa_aviso.style().polish(self.faixa_aviso)
        self.faixa_aviso.setText(texto)
        self.faixa_aviso.show()
        self._timer_aviso.start(9000 if tipo == "erro" else 6000)

    def limpar_aviso(self):
        self.faixa_aviso.hide()
        self.faixa_aviso.setText("")

    def tentar(self, funcao, *args, **kwargs):
        """Chama um service; se ele recusar, mostra o motivo e devolve FALHOU."""
        try:
            return funcao(*args, **kwargs)
        except Exception as erro:
            self.aviso(c.mensagem_de_erro(erro), "erro")
            return self.FALHOU

    @property
    def perfil(self):
        return sessao.usuario.tipo if sessao.logado else None

    # ------------------------------------------------------------ navegação
    def mostrar(self, tela):
        """Troca a tela, respeitando o perfil de quem está logado. Devolve True se trocou."""
        self.limpar_aviso()
        if tela is self.tela_acesso:
            if sessao.logado:
                return self.ir_para_inicio()
        elif not sessao.logado:
            self.ir_para_acesso()
            self.aviso("Entre na sua conta para continuar.", "erro")
            return False
        else:
            exigido = self._perfil_da_tela.get(tela)
            if exigido and exigido != sessao.usuario.tipo:
                self.aviso(
                    "Esta área é exclusiva de professores." if exigido == "professor" else "Esta área é exclusiva de alunos.",
                    "erro",
                )
                return False
        self.pilha.setCurrentWidget(tela)
        self._atualizar_barra()
        return True

    def ir_para_acesso(self):
        self.tela_acesso.reiniciar()
        self.pilha.setCurrentWidget(self.tela_acesso)
        self._atualizar_barra()

    def ir_para_inicio(self):
        if not sessao.logado:
            self.ir_para_acesso()
            return False
        if sessao.usuario.tipo == "professor":
            return self.abrir_turmas_professor()
        return self.abrir_turmas()

    def _abrir(self, tela, carregar, *args):
        if self.perfil is None:
            return self.mostrar(tela)  # manda para o acesso com o aviso
        exigido = self._perfil_da_tela.get(tela)
        if exigido and exigido != self.perfil:
            return self.mostrar(tela)  # recusa antes de carregar qualquer dado
        if self.tentar(carregar, *args) is self.FALHOU:
            return False
        return self.mostrar(tela)

    def abrir_turmas(self):
        return self._abrir(self.tela_turmas, self.tela_turmas.carregar)

    def abrir_pesquisas(self, turma_id, visao="individuais"):
        """A turma do aluno: visao 'individuais' ou 'grupos'."""
        return self._abrir(self.tela_pesquisas, self.tela_pesquisas.carregar, turma_id, visao)

    def abrir_pesquisa(self, pesquisa_id):
        return self._abrir(self.tela_pesquisa, self.tela_pesquisa.carregar, pesquisa_id)

    def abrir_interacao(self, interacao_id):
        return self._abrir(self.tela_interacao, self.tela_interacao.carregar, interacao_id)

    def abrir_relatorio(self, pesquisa_id, texto_voltar, acao_voltar):
        return self._abrir(self.tela_relatorio, self.tela_relatorio.carregar, pesquisa_id, texto_voltar, acao_voltar)

    def abrir_turmas_professor(self):
        return self._abrir(self.tela_turmas_professor, self.tela_turmas_professor.carregar)

    def abrir_turma_professor(self, turma_id, visao="alunos"):
        """A turma do professor: visao 'alunos' ou 'grupos'."""
        return self._abrir(self.tela_turma_professor, self.tela_turma_professor.carregar, turma_id, visao)

    def abrir_professor(self, turma_id=None):
        """Lista de pesquisas das turmas do professor, todas ou só de uma (turma_id)."""
        return self._abrir(self.tela_professor, self.tela_professor.carregar, turma_id)

    def abrir_revisao(self, pesquisa_id):
        return self._abrir(self.tela_revisao, self.tela_revisao.carregar, pesquisa_id)

    def abrir_revisao_interacao(self, interacao_id):
        return self._abrir(self.tela_revisao_interacao, self.tela_revisao_interacao.carregar, interacao_id)

    def entrou(self):
        """Chamado pela tela de acesso depois de um login bem-sucedido."""
        self.ir_para_inicio()

    def sair(self):
        self.usuarios.sair()
        self.ir_para_acesso()
        self.aviso("Você saiu da conta.", "info")
