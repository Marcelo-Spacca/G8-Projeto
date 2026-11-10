"""Menu de texto para testar os services na prática."""
import getpass

from services.erros import RegraViolada
from services.fonte_service import FonteService
from services.interacao_service import InteracaoService
from services.pesquisa_service import PesquisaService
from services.relatorio_service import RelatorioService
from services.sessao import sessao
from services.usuario_service import UsuarioService

STATUS = {"em_andamento": "Em andamento", "concluida": "Concluída"}
STATUS_FONTE = {"nao_verificada": "Não verificada", "verificada": "Verificada", "incorreta": "Incorreta"}
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
        self.fontes = FonteService()
        self.relatorios = RelatorioService()

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

    def _confirmar(self, pergunta):
        return self._ler(f"{pergunta} (s/n)").lower() in ("s", "sim")

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
                self.saida("1. Listar pesquisas dos alunos\n2. Ver relatório de uma pesquisa\n0. Sair da conta")
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
            elif usuario.tipo == "professor" and opcao == "1":
                self._seguro(self._listar_pesquisas_professor)
            elif usuario.tipo == "professor" and opcao == "2":
                self._seguro(self._relatorio_professor)
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

    def _listar_pesquisas_professor(self):
        lista = self.relatorios.listar_pesquisas()
        if not lista:
            self.saida("\nNenhum aluno criou pesquisas ainda.")
            return lista
        self.saida(f"\n{'Nº':>3}  {'Título':<30} {'Aluno':<18} {'Status':<13} Criada em")
        for n, p in enumerate(lista, 1):
            self.saida(
                f"{n:>3}  {_cortar(p.titulo, 30):<30} {_cortar(p.aluno.nome, 18):<18} "
                f"{STATUS[p.status]:<13} {_data(p.data_criacao)}"
            )
        return lista

    def _relatorio_professor(self):  # RF20
        lista = self._listar_pesquisas_professor()
        if not lista:
            return
        pesquisa = self._escolher_numero(lista, "Número da pesquisa")
        if pesquisa:
            self._mostrar_relatorio(self.relatorios.gerar(pesquisa.id))

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
            self.saida(
                "1. Registrar interação\n2. Listar interações\n"
                "3. Abrir uma interação (ver, editar, excluir, fontes)\n"
                "4. Editar título e objetivo\n5. Ver relatório desta pesquisa\n0. Voltar"
                "1. Registrar interação\n2. Listar interações\n3. Ver uma interação (pergunta e resposta)\n"
                "4. Editar título e objetivo\n0. Voltar"
            )
            opcao = self._ler("Escolha")
            if opcao == "0":
                return
            elif opcao == "1":
                self._seguro(self._registrar_interacao, pesquisa_id)
            elif opcao == "2":
                self._seguro(self._listar_interacoes, pesquisa_id)
            elif opcao == "3":
                self._seguro(self._ver_interacao, pesquisa_id)
            elif opcao == "4":
                self._seguro(self._editar_pesquisa, pesquisa_id)
            elif opcao == "5":
                self._seguro(self._relatorio_aluno, pesquisa_id)
            else:
                self.saida("Opção inválida.")

    def _editar_pesquisa(self, pesquisa_id):  # RF08
        atual = self.pesquisas.obter(pesquisa_id)
        self.saida("Deixe em branco (Enter) para manter o valor atual.")
        titulo = self._ler(f"Novo título [{_cortar(atual.titulo, 40)}]") or atual.titulo
        objetivo = self._ler(f"Novo objetivo [{_cortar(atual.objetivo, 40)}]") or atual.objetivo
        pesquisa = self.pesquisas.editar(pesquisa_id, titulo, objetivo)
        self.saida(f"\nPesquisa atualizada: {pesquisa.titulo}")

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
            self._menu_interacao(interacao.id)

    def _relatorio_aluno(self, pesquisa_id):  # RF20
        self._mostrar_relatorio(self.relatorios.gerar(pesquisa_id))

    # ------------------------------------------------------------ dentro de uma interação
    def _mostrar_interacao(self, interacao):
        self.saida(f"\n{LINHA}")
        self.saida(f"Ferramenta: {interacao.ferramenta_ia}   |   Registrada em: {_data(interacao.data_registro)}")
        self.saida(f"{LINHA}\nPERGUNTA:\n{interacao.pergunta}\n\nRESPOSTA DA IA:\n{interacao.resposta}\n{LINHA}")
        # RF27: cada fonte aparece com os trechos ligados a ela logo abaixo
        fontes = _ordenar_fontes(interacao)
        self.saida("FONTES:" if fontes else "FONTES: nenhuma fonte registrada.")
        for n, fonte in enumerate(fontes, 1):
            self.saida(f"{n:>3}. {fonte.referencia}  [{STATUS_FONTE[fonte.status]}]")
            if fonte.anotacao_correcao:
                self.saida(f"       Anotação: {fonte.anotacao_correcao}")
            for trecho in _ordenar_trechos(fonte):
                self.saida(f"       -> {_trecho(trecho)}")
        self.saida(LINHA)

    def _menu_interacao(self, interacao_id):
        while True:
            try:
                interacao = self.interacoes.obter(interacao_id)
            except RegraViolada as erro:
                self.saida(f"\n[ERRO] {erro}")
                return
            self._mostrar_interacao(interacao)
            self.saida(
                "1. Editar interação\n2. Excluir interação\n3. Adicionar fonte\n"
                "4. Verificar fonte\n5. Ligar outro trecho a uma fonte verificada\n0. Voltar"
            )
            opcao = self._ler("Escolha")
            if opcao == "0":
                return
            elif opcao == "1":
                self._seguro(self._editar_interacao, interacao)
            elif opcao == "2":
                if self._seguro(self._excluir_interacao, interacao):
                    return
            elif opcao == "3":
                self._seguro(self._adicionar_fonte, interacao)
            elif opcao == "4":
                self._seguro(self._verificar_fonte, interacao)
            elif opcao == "5":
                self._seguro(self._ligar_trecho, interacao)
            else:
                self.saida("Opção inválida.")

    def _editar_interacao(self, interacao):  # RF13
        self.saida("Deixe em branco para manter o valor atual.")
        ferramenta = self._ler(f"Ferramenta de IA [{interacao.ferramenta_ia}]") or interacao.ferramenta_ia
        pergunta = self._ler_texto("Nova pergunta").strip() or interacao.pergunta
        resposta = self._ler_texto("Nova resposta da IA").strip() or interacao.resposta
        self.interacoes.editar(interacao.id, ferramenta, pergunta, resposta)
        self.saida("\nInteração atualizada. As fontes ligadas foram mantidas.")

    def _excluir_interacao(self, interacao):  # RF14
        qtd = len(interacao.fontes)
        aviso = f" e suas {qtd} fonte(s)" if qtd else ""
        if not self._confirmar(f"Excluir esta interação{aviso}? Isso não pode ser desfeito"):
            self.saida("Exclusão cancelada.")
            return False
        self.interacoes.excluir(interacao.id)
        self.saida("\nInteração excluída.")
        return True

    def _adicionar_fonte(self, interacao):
        referencia = self._ler("Referência da fonte citada pela IA")
        self.fontes.adicionar(interacao.id, referencia)
        self.saida("\nFonte adicionada.")

    def _escolher_fonte(self, interacao):
        fontes = _ordenar_fontes(interacao)
        if not fontes:
            self.saida("\nEsta interação ainda não tem fontes.")
            return None
        return self._escolher_numero(fontes, "Número da fonte")

    def _verificar_fonte(self, interacao):  # RF26 + RF18
        fonte = self._escolher_fonte(interacao)
        if not fonte:
            return
        resultado = {"1": "verificada", "2": "incorreta"}.get(
            self._ler("Resultado (1 = verificada, 2 = incorreta)"), ""
        )
        anotacao = self._ler_texto("Anotação sobre o que você encontrou (opcional)")
        trecho = localizacao = None
        if resultado == "verificada" and self._confirmar("Quer ligar esta fonte a um trecho do seu texto?"):
            trecho = self._ler_texto("Trecho do seu texto")
            localizacao = self._ler("Onde está o trecho (parágrafo/linha, opcional)")
        self.fontes.verificar(fonte.id, resultado, anotacao, trecho, localizacao)
        self.saida("\nVerificação salva.")

    def _ligar_trecho(self, interacao):  # RF26
        fonte = self._escolher_fonte(interacao)
        if not fonte:
            return
        trecho = self._ler_texto("Trecho do seu texto")
        localizacao = self._ler("Onde está o trecho (parágrafo/linha, opcional)")
        self.fontes.ligar_trecho(fonte.id, trecho, localizacao)
        self.saida("\nTrecho ligado à fonte.")

    # ------------------------------------------------------------ relatório
    def _mostrar_relatorio(self, gerado):  # RF20 / RF22
        p = gerado.pesquisa
        contagem = gerado.contagem_status()
        self._titulo("RELATÓRIO DE USO DE IA")
        self.saida(f"Pesquisa: {p.titulo} [{STATUS[p.status]}]")
        self.saida(f"Aluno: {p.aluno.nome}")
        self.saida(f"Objetivo: {p.objetivo}")
        self.saida(f"Gerado em: {_data(gerado.relatorio.data_geracao)}")
        self.saida(
            f"Resumo: {len(gerado.interacoes)} interação(ões), {len(gerado.fontes)} fonte(s) — "
            f"{contagem['verificada']} verificada(s), {contagem['incorreta']} incorreta(s), "
            f"{contagem['nao_verificada']} não verificada(s)"
        )
        if not gerado.interacoes:
            self.saida("\nNenhuma interação registrada nesta pesquisa.")
        for n, i in enumerate(gerado.interacoes, 1):
            self.saida(f"\n[{n}] {i.ferramenta_ia} — {_data(i.data_registro)}")
            self.saida(f"PERGUNTA:\n{i.pergunta}\nRESPOSTA DA IA:\n{i.resposta}")
            fontes = _ordenar_fontes(i)
            self.saida("Fontes:" if fontes else "Fontes: nenhuma")
            for fonte in fontes:
                self.saida(f"  - {fonte.referencia}  [{STATUS_FONTE[fonte.status]}]")
                if fonte.anotacao_correcao:
                    self.saida(f"      Anotação do aluno: {fonte.anotacao_correcao}")
                for trecho in _ordenar_trechos(fonte):
                    self.saida(f"      {_trecho(trecho)}")
        self.saida(LINHA)


def _ordenar_fontes(interacao):
    return sorted(interacao.fontes, key=lambda f: f.id)


def _ordenar_trechos(fonte):
    return sorted(fonte.trechos, key=lambda t: t.id)


def _trecho(trecho):
    onde = f" ({trecho.localizacao})" if trecho.localizacao else ""
    return f'Trecho{onde}: "{trecho.trecho_citado}"'
            self.saida(f"\n{LINHA}")
            self.saida(f"Ferramenta: {interacao.ferramenta_ia}   |   Registrada em: {_data(interacao.data_registro)}")
            self.saida(f"{LINHA}\nPERGUNTA:\n{interacao.pergunta}\n\nRESPOSTA DA IA:\n{interacao.resposta}\n{LINHA}")
