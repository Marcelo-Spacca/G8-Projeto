"""Menu de texto para testar os services na prática."""
import getpass

from services.erros import RegraViolada
from services.interacao_service import InteracaoService
from services.pesquisa_service import PesquisaService
from services.sessao import sessao
from services.usuario_service import UsuarioService

STATUS = {"em_andamento": "Em andamento", "concluida": "Concluída"}
LINHA = "=" * 56
FIM = "FIM"


def _cortar(texto, limite):
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 3] + "..."


def _data(valor):
    return valor.strftime("%d/%m/%Y %H:%M")


class MenuConsole:
    # entrada, saida e senha podem ser trocadas nos testes automáticos
    def __init__(self, entrada=input, saida=print, senha=getpass.getpass):
        self.entrada = entrada
        self.saida = saida
        self.senha = senha
        self.usuarios = UsuarioService()
        self.pesquisas = PesquisaService()
        self.interacoes = InteracaoService()

    # ------------------------------------------------------------ utilitários
    def _ler(self, rotulo):
        return self.entrada(f"{rotulo}: ").strip()

    def _ler_texto(self, rotulo):
        self.saida(f"{rotulo} (digite ou cole; termine com uma linha só com {FIM}):")
        linhas = []
        while True:
            linha = self.entrada("> ")
            if linha.strip().upper() == FIM:
                return "\n".join(linhas)
            linhas.append(linha)

    def _titulo(self, texto):
        self.saida(f"\n{LINHA}\n {texto}\n{LINHA}")

    def _seguro(self, acao, *args):
        try:
            return acao(*args)
        except RegraViolada as erro:
            self.saida(f"\n[ERRO] {erro}")
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception as erro:  # banco fora do ar, .env errado, bug...
            primeira_linha = (str(erro).splitlines() or [""])[0]
            self.saida(f"\n[ERRO INESPERADO] {type(erro).__name__}: {primeira_linha}")
            self.saida("Se for de conexão, confira se o PostgreSQL está rodando e o arquivo .env.")

    def _escolher_numero(self, itens, rotulo):
        resposta = self._ler(f"{rotulo} (Enter para voltar)")
        if not resposta:
            return None
        if not resposta.isdigit() or not 1 <= int(resposta) <= len(itens):
            self.saida("Número inválido.")
            return None
        return itens[int(resposta) - 1]

    # ------------------------------------------------------------ menu inicial
    def executar(self):
        try:
            self._menu_inicial()
        except (EOFError, KeyboardInterrupt):
            self.saida("\nAté logo!")

    def _menu_inicial(self):
        while True:
            self._titulo("Registro verificável do uso de IA (console)")
            self.saida("1. Cadastrar\n2. Entrar\n0. Sair do programa")
            opcao = self._ler("Escolha")
            if opcao == "1":
                self._seguro(self._cadastrar)
            elif opcao == "2":
                self._seguro(self._entrar)
                if sessao.logado:
                    self._menu_logado()
            elif opcao == "0":
                self.saida("Até logo!")
                return
            else:
                self.saida("Opção inválida.")

    def _cadastrar(self):  # RF01
        nome = self._ler("Nome")
        email = self._ler("E-mail")
        senha = self.senha("Senha (mínimo 6 caracteres): ")
        perfil = self._ler("Perfil (1 = aluno, 2 = professor)")
        tipo = {"1": "aluno", "2": "professor"}.get(perfil, "")
        usuario = self.usuarios.cadastrar(nome, email, senha, tipo)
        self.saida(f"\nConta criada: {usuario.nome} <{usuario.email}> ({usuario.tipo}). Agora escolha 'Entrar'.")

    def _entrar(self):  # RF02
        email = self._ler("E-mail")
        senha = self.senha("Senha: ")
        usuario = self.usuarios.entrar(email, senha)
        self.saida(f"\nBem-vindo(a), {usuario.nome}!")

    # ------------------------------------------------------------ usuário logado
    def _menu_logado(self):
        usuario = sessao.usuario
        while sessao.logado:
            self._titulo(f"Olá, {usuario.nome} ({usuario.tipo})")
            if usuario.tipo == "aluno":
                self.saida("1. Criar pesquisa\n2. Listar minhas pesquisas\n3. Abrir uma pesquisa\n0. Sair da conta")
            else:
                self.saida("(A área do professor ainda não foi implementada.)\n0. Sair da conta")
            opcao = self._ler("Escolha")
            if opcao == "0":
                self.usuarios.sair()
                self.saida("Você saiu da conta.")
                return
            if usuario.tipo == "aluno" and opcao == "1":
                self._seguro(self._criar_pesquisa)
            elif usuario.tipo == "aluno" and opcao == "2":
                self._seguro(self._listar_pesquisas)
            elif usuario.tipo == "aluno" and opcao == "3":
                self._seguro(self._abrir_pesquisa)
            else:
                self.saida("Opção inválida.")

    def _criar_pesquisa(self):  # RF06
        titulo = self._ler("Título da pesquisa")
        objetivo = self._ler("Objetivo da pesquisa")
        pesquisa = self.pesquisas.criar(titulo, objetivo)
        self.saida(f"\nPesquisa criada: {pesquisa.titulo} [{STATUS[pesquisa.status]}]")

    def _listar_pesquisas(self):  # RF07
        lista = self.pesquisas.listar_minhas()
        if not lista:
            self.saida("\nVocê ainda não criou nenhuma pesquisa.")
            return lista
        self.saida(f"\n{'Nº':>3}  {'Título':<34} {'Status':<13} Criada em")
        for n, p in enumerate(lista, 1):
            self.saida(f"{n:>3}  {_cortar(p.titulo, 34):<34} {STATUS[p.status]:<13} {_data(p.data_criacao)}")
        return lista

    def _abrir_pesquisa(self):
        lista = self._listar_pesquisas()
        if not lista:
            return
        pesquisa = self._escolher_numero(lista, "Número da pesquisa")
        if pesquisa:
            self._menu_pesquisa(pesquisa.id)

    # ------------------------------------------------------------ dentro de uma pesquisa
    def _menu_pesquisa(self, pesquisa_id):
        while True:
            try:
                pesquisa = self.pesquisas.obter(pesquisa_id)
            except RegraViolada as erro:
                self.saida(f"\n[ERRO] {erro}")
                return
            self._titulo(f"Pesquisa: {_cortar(pesquisa.titulo, 40)} [{STATUS[pesquisa.status]}]")
            self.saida(f"Objetivo: {pesquisa.objetivo}\n")
            self.saida("1. Registrar interação\n2. Listar interações\n3. Ver uma interação (pergunta e resposta)\n0. Voltar")
            opcao = self._ler("Escolha")
            if opcao == "0":
                return
            elif opcao == "1":
                self._seguro(self._registrar_interacao, pesquisa_id)
            elif opcao == "2":
                self._seguro(self._listar_interacoes, pesquisa_id)
            elif opcao == "3":
                self._seguro(self._ver_interacao, pesquisa_id)
            else:
                self.saida("Opção inválida.")

    def _registrar_interacao(self, pesquisa_id):  # RF11
        ferramenta = self._ler("Ferramenta de IA (ex.: ChatGPT, Claude, Gemini)")
        pergunta = self._ler_texto("Pergunta")
        resposta = self._ler_texto("Resposta da IA")
        self.interacoes.registrar(pesquisa_id, ferramenta, pergunta, resposta)
        self.saida("\nInteração registrada.")

    def _listar_interacoes(self, pesquisa_id):  # RF12
        lista = self.interacoes.listar(pesquisa_id)
        if not lista:
            self.saida("\nNenhuma interação registrada nesta pesquisa.")
            return lista
        self.saida(f"\n{'Nº':>3}  {'Registrada em':<16} {'Ferramenta':<12} Pergunta")
        for n, i in enumerate(lista, 1):
            self.saida(f"{n:>3}  {_data(i.data_registro):<16} {_cortar(i.ferramenta_ia, 12):<12} {_cortar(i.pergunta, 40)}")
        return lista

    def _ver_interacao(self, pesquisa_id):
        lista = self._listar_interacoes(pesquisa_id)
        if not lista:
            return
        interacao = self._escolher_numero(lista, "Número da interação")
        if interacao:
            self.saida(f"\n{LINHA}")
            self.saida(f"Ferramenta: {interacao.ferramenta_ia}   |   Registrada em: {_data(interacao.data_registro)}")
            self.saida(f"{LINHA}\nPERGUNTA:\n{interacao.pergunta}\n\nRESPOSTA DA IA:\n{interacao.resposta}\n{LINHA}")
