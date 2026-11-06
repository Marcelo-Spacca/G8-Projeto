"""Menu de console. Só lê o que o usuário digita, chama os services e mostra o resultado."""

from getpass import getpass

from services.servicos import (
    ConteudoRelatorio,
    FonteService,
    InteracaoService,
    PesquisaService,
    RegraViolada,
    RelatorioService,
    UsuarioService,
)

STATUS_LEGIVEL = {
    "nao_verificada": "não verificada",
    "verificada": "verificada",
    "incorreta": "incorreta",
}


# --------------------------------------------------------------------------- entrada


def ler_texto_longo(rotulo: str) -> str:
    print(f"{rotulo} (termine com uma linha contendo só FIM):")
    linhas = []
    while (linha := input()) != "FIM":
        linhas.append(linha)
    return "\n".join(linhas)


def ler_int(rotulo: str) -> int | None:
    valor = input(rotulo).strip()
    return int(valor) if valor.isdigit() else None


def confirmar(pergunta: str) -> bool:
    return input(f"{pergunta} (s/n): ").strip().lower() in ("s", "sim")


# --------------------------------------------------------------------------- menu


class MenuConsole:
    def __init__(self):
        self.usuarios = UsuarioService()
        self.pesquisas = PesquisaService()
        self.interacoes = InteracaoService()
        self.fontes = FonteService()
        self.relatorios = RelatorioService()
        self.usuario = None

    def executar(self):
        while True:
            try:
                if self.usuario is None:
                    if not self.menu_inicial():
                        break
                elif self.usuario.tipo == "aluno":
                    self.menu_aluno()
                else:
                    self.menu_professor()
            except RegraViolada as e:
                print(f"\n[!] {e}\n")
            except (KeyboardInterrupt, EOFError):
                print("\nAté logo!")
                break

    # ---------------------------------------------------------------- início

    def menu_inicial(self) -> bool:
        print("\n=== Registro verificável do uso de IA ===")
        print("1) Cadastrar\n2) Entrar\n0) Sair")
        op = input("> ").strip()
        if op == "1":
            nome = input("Nome: ")
            email = input("E-mail: ")
            senha = getpass("Senha: ")
            tipo = "professor" if input("Tipo (a=aluno, p=professor): ").strip() == "p" else "aluno"
            self.usuarios.cadastrar(nome, email, senha, tipo)
            print("Cadastro feito! Agora é só entrar.")
        elif op == "2":
            self.usuario = self.usuarios.entrar(input("E-mail: "), getpass("Senha: "))
            print(f"Olá, {self.usuario.nome}!")
        elif op == "0":
            return False
        return True

    # ---------------------------------------------------------------- aluno

    def menu_aluno(self):
        print("\n--- Menu do aluno ---")
        print("1) Criar pesquisa\n2) Minhas pesquisas\n3) Abrir pesquisa\n0) Sair da conta")
        op = input("> ").strip()
        if op == "1":
            p = self.pesquisas.criar(
                self.usuario.id, input("Título: "), ler_texto_longo("Objetivo")
            )
            print(f"Pesquisa #{p.id} criada (o relatório dela é gerado automaticamente).")
        elif op == "2":
            self.listar_pesquisas()
        elif op == "3":
            self.listar_pesquisas()
            pid = ler_int("Número da pesquisa: ")
            if pid:
                self.menu_pesquisa(pid)
        elif op == "0":
            self.usuario = None

    def listar_pesquisas(self):
        pesquisas = self.pesquisas.listar_do_aluno(self.usuario.id)
        if not pesquisas:
            print("Nenhuma pesquisa ainda.")
        for p in pesquisas:
            print(f"  #{p.id} {p.titulo} [{p.status}]")

    def menu_pesquisa(self, pesquisa_id: int):
        while True:
            try:
                interacoes = self.interacoes.listar(self.usuario.id, pesquisa_id)
                print(f"\n--- Pesquisa #{pesquisa_id} ---")
                for i in interacoes:
                    print(f"  #{i.id} [{i.ferramenta_ia}] {resumo(i.pergunta)} ({len(i.fontes)} fonte(s))")
                print(
                    "1) Registrar interação\n2) Abrir interação\n3) Ver relatório desta pesquisa\n0) Voltar"
                )
                op = input("> ").strip()
                if op == "1":
                    ferramenta = input("Ferramenta de IA (ex.: ChatGPT): ")
                    pergunta = ler_texto_longo("Pergunta")
                    resposta = ler_texto_longo("Resposta da IA")
                    fontes = ler_texto_longo("Fontes citadas pela IA, uma por linha")
                    i = self.interacoes.registrar(
                        self.usuario.id, pesquisa_id, ferramenta, pergunta, resposta, fontes.splitlines()
                    )
                    print(f"Interação #{i.id} registrada.")
                elif op == "2":
                    iid = ler_int("Número da interação: ")
                    if iid:
                        self.menu_interacao(iid)
                elif op == "3":
                    mostrar_relatorio(self.relatorios.gerar(self.usuario, pesquisa_id))
                elif op == "0":
                    return
            except RegraViolada as e:
                print(f"\n[!] {e}\n")

    def menu_interacao(self, interacao_id: int):
        while True:
            try:
                i = self.interacoes.obter(self.usuario.id, interacao_id)
                mostrar_interacao(i)
                print(
                    "1) Editar interação\n2) Excluir interação\n3) Adicionar fonte\n"
                    "4) Verificar fonte\n5) Ligar outro trecho a uma fonte verificada\n0) Voltar"
                )
                op = input("> ").strip()
                if op == "1":  # RF13
                    print("Deixe em branco (ou só FIM) para manter o valor atual.")
                    ferramenta = input(f"Ferramenta de IA [{i.ferramenta_ia}]: ")
                    pergunta = ler_texto_longo("Nova pergunta")
                    resposta = ler_texto_longo("Nova resposta")
                    self.interacoes.editar(self.usuario.id, i.id, ferramenta, pergunta, resposta)
                    print("Interação atualizada. As fontes ligadas foram mantidas.")
                elif op == "2":  # RF14
                    aviso = f" e suas {len(i.fontes)} fonte(s)" if i.fontes else ""
                    if confirmar(f"Excluir a interação #{i.id}{aviso}? Isso não pode ser desfeito"):
                        self.interacoes.excluir(self.usuario.id, i.id)
                        print("Interação excluída.")
                        return
                    print("Exclusão cancelada.")
                elif op == "3":
                    self.fontes.adicionar(self.usuario.id, i.id, input("Referência da fonte: "))
                    print("Fonte adicionada.")
                elif op == "4":  # RF26 + RF18
                    fid = ler_int("Número da fonte: ")
                    if not fid:
                        continue
                    verificada = input("A fonte é válida? (s = verificada, n = incorreta): ").strip().lower()
                    status = "verificada" if verificada in ("s", "sim") else "incorreta"
                    anotacao = ler_texto_longo("Anotação sobre o que você encontrou (opcional)")
                    trecho = local = None
                    if status == "verificada" and confirmar("Quer ligar esta fonte a um trecho do seu texto?"):
                        trecho = ler_texto_longo("Trecho do seu texto")
                        local = input("Onde está o trecho (parágrafo/linha, opcional): ")
                    self.fontes.verificar(self.usuario.id, fid, status, anotacao, trecho, local)
                    print("Verificação salva.")
                elif op == "5":  # RF26
                    fid = ler_int("Número da fonte: ")
                    if fid:
                        self.fontes.vincular_trecho(
                            self.usuario.id,
                            fid,
                            ler_texto_longo("Trecho do seu texto"),
                            input("Onde está o trecho (parágrafo/linha, opcional): "),
                        )
                        print("Trecho ligado à fonte.")
                elif op == "0":
                    return
            except RegraViolada as e:
                print(f"\n[!] {e}\n")

    # ---------------------------------------------------------------- professor

    def menu_professor(self):
        print("\n--- Menu do professor ---")
        print("1) Listar pesquisas\n2) Ver relatório de uma pesquisa\n0) Sair da conta")
        op = input("> ").strip()
        if op == "1":
            for p in self.pesquisas.listar_todas():
                print(f"  #{p.id} {p.titulo} — {p.aluno.nome} [{p.status}]")
        elif op == "2":
            pid = ler_int("Número da pesquisa: ")
            if pid:
                mostrar_relatorio(self.relatorios.gerar(self.usuario, pid))
        elif op == "0":
            self.usuario = None


# --------------------------------------------------------------------------- exibição


def resumo(texto: str, n: int = 60) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= n else texto[: n - 1] + "…"


def mostrar_interacao(i):
    """RF27: cada fonte aparece com os trechos ligados a ela ao lado."""
    print(f"\n=== Interação #{i.id} — {i.ferramenta_ia} ===")
    print(f"Pergunta:\n{i.pergunta}\n")
    print(f"Resposta:\n{i.resposta}\n")
    print("Fontes:")
    if not i.fontes:
        print("  (nenhuma)")
    for f in sorted(i.fontes, key=lambda f: f.id):
        print(f"  #{f.id} {f.referencia}  [{STATUS_LEGIVEL[f.status]}]")
        if f.anotacao_correcao:
            print(f"      Anotação: {f.anotacao_correcao}")
        for t in f.trechos:
            onde = f" ({t.localizacao})" if t.localizacao else ""
            print(f"      ↳ Trecho{onde}: \"{t.trecho_citado}\"")
    print()


def formatar_relatorio(r: ConteudoRelatorio) -> str:
    linhas = [
        f"RELATÓRIO DE USO DE IA — #{r.relatorio_id}",
        f"Pesquisa #{r.pesquisa_id}: {r.titulo}",
        f"Aluno: {r.aluno}",
        f"Gerado em: {r.data_geracao:%d/%m/%Y %H:%M}",
        f"Objetivo: {r.objetivo}",
        "",
    ]
    c = r.contagem_status()
    linhas.append(
        f"Resumo: {len(r.interacoes)} interação(ões), {r.total_fontes} fonte(s) — "
        f"{c['verificada']} verificada(s), {c['incorreta']} incorreta(s), "
        f"{c['nao_verificada']} não verificada(s)."
    )
    for n, i in enumerate(r.interacoes, 1):
        linhas += [
            "",
            f"[{n}] {i.ferramenta_ia} — {i.data_registro:%d/%m/%Y %H:%M}",
            f"  Pergunta: {i.pergunta}",
            f"  Resposta: {i.resposta}",
            "  Fontes:" if i.fontes else "  Fontes: (nenhuma)",
        ]
        for f in i.fontes:
            linhas.append(f"    - {f.referencia} [{STATUS_LEGIVEL.get(f.status, f.status)}]")
            if f.anotacao:
                linhas.append(f"        Anotação do aluno: {f.anotacao}")
            for t in f.trechos:
                onde = f" ({t.localizacao})" if t.localizacao else ""
                linhas.append(f"        Trecho{onde}: \"{t.texto}\"")
    return "\n".join(linhas)


def mostrar_relatorio(r: ConteudoRelatorio):
    print("\n" + formatar_relatorio(r) + "\n")
