"""Popula o banco com dados de exemplo (professores, alunos, turmas, grupos, pesquisas...) para
testar o programa sem cadastrar tudo à mão.

    python -m scripts.popular_exemplo             # cria os dados (se ainda não existirem)
    python -m scripts.popular_exemplo --limpar    # apaga só os dados de exemplo
    python -m scripts.popular_exemplo --recriar   # apaga e cria de novo

Tudo usa e-mails @exemplo.com e a senha "senha123", então dá para apagar sem tocar no que você
cadastrou de verdade. Os dados passam pelos mesmos services do programa, ou seja, seguem as regras
reais (estados da pesquisa, convites, revisão do professor).
"""
import sys

from repository import armazenamento
from repository.models import Turma
from repository.turma_repository import TurmaRepository
from repository.usuario_repository import UsuarioRepository
from services.fonte_service import FonteService
from services.grupo_service import GrupoService
from services.interacao_service import InteracaoService
from services.pesquisa_service import PesquisaService
from services.revisao_service import RevisaoService
from services.sessao import sessao
from services.usuario_service import UsuarioService

SENHA = "senha123"
DOMINIO = "@exemplo.com"
PROFESSORES = {
    "marina": "Profa. Marina Lopes",
    "carlos": "Prof. Carlos Teixeira",
}
ALUNOS = {
    "ana": "Ana Souza",
    "bia": "Bia Ferreira",
    "caio": "Caio Mendes",
    "dani": "Dani Rocha",
    "edu": "Eduardo Lima",
    "fabi": "Fabiana Alves",
}


def email(apelido):
    return f"{apelido}{DOMINIO}"


def limpar():
    """Apaga os usuários de exemplo e, em cascata (feita pelo repositório), as turmas dos
    professores (com matrículas, grupos, convites e pesquisas) e as pesquisas dos alunos."""
    repo = UsuarioRepository()
    exemplos = repo.listar_com_email_terminando_em(DOMINIO)
    for usuario in exemplos:
        repo.excluir(usuario.id)
    print(f"Dados de exemplo apagados ({len(exemplos)} usuários e tudo o que dependia deles).")


def ja_existe():
    return UsuarioRepository().buscar_por_email(email("ana")) is not None


def popular():
    usuarios, turmas_repo = UsuarioService(), TurmaRepository()
    pesquisas, interacoes, fontes = PesquisaService(), InteracaoService(), FonteService()
    grupos, revisoes = GrupoService(), RevisaoService()

    def como(apelido):
        sessao.encerrar()
        usuarios.entrar(email(apelido), SENHA)
        return sessao.usuario

    # ------------------------------------------------------------ contas
    for apelido, nome in {**PROFESSORES, **ALUNOS}.items():
        tipo = "professor" if apelido in PROFESSORES else "aluno"
        usuarios.cadastrar(nome, email(apelido), SENHA, tipo)

    # ------------------------------------------------------------ turmas (códigos fixos, fáceis de digitar)
    def turma(dono, nome, codigo, permite_grupos):
        return turmas_repo.salvar(
            Turma(nome=nome, codigo=codigo, permite_grupos=permite_grupos, professor_id=como(dono).id)
        )

    projeto = turma("marina", "Projeto 1, SI 26.2", "PROJ01", True)
    banco = turma("marina", "Banco de Dados", "BANCO1", False)
    redes = turma("carlos", "Redes de Computadores", "REDES1", False)

    from services.turma_service import TurmaService

    entrar = TurmaService().entrar
    for apelido in ("ana", "bia", "caio", "dani", "edu"):
        como(apelido)
        entrar(projeto.codigo)
    for apelido in ("ana", "edu"):
        como(apelido)
        entrar(banco.codigo)
    como("edu")
    entrar(redes.codigo)
    # a Fabiana fica sem turma de propósito: dá para testar a entrada pelo código (PROJ01)

    # ------------------------------------------------------------ pesquisas individuais
    def interacao(pesquisa, ferramenta, pergunta, resposta, *fontes_):
        i = interacoes.registrar(pesquisa.id, ferramenta, pergunta, resposta)
        return i, [fontes.adicionar(i.id, ref, link) for ref, link in fontes_]

    # Ana: em andamento, com fontes verificada (com trecho), incorreta e pendente
    como("ana")
    p_ana = pesquisas.criar(projeto.id, "Impactos da IA na educação superior",
                            "Entender como estudantes de graduação usam IA em trabalhos e quais riscos isso traz.")
    i1, (f1, f2, f3) = interacao(
        p_ana, "ChatGPT", "Quais os principais impactos da IA no ensino superior?",
        "Pesquisas apontam ganho de produtividade, mas também risco de dependência e de plágio [1][2].",
        ("SILVA, J. A educação na era da IA. Revista Brasileira de Educação, 2023.", "https://exemplo.org/silva-2023"),
        ("MENDES, C. Plágio e inteligência artificial. Editora Atlas, 2022.", None),
        ("TANAKA, K. Neural tutoring at scale. Journal of Learning, 2021.", "https://exemplo.org/tanaka"),
    )
    fontes.verificar(f1.id, "verificada", "Artigo existe e confirma o que a IA disse.",
                     "A IA aumenta a produtividade, mas exige leitura crítica das respostas.", "parágrafo 2")
    fontes.verificar(f2.id, "incorreta", "Não encontrei este livro em nenhuma biblioteca ou catálogo.")
    interacao(p_ana, "Claude", "Como citar o uso de IA em um trabalho acadêmico?",
              "Informe a ferramenta, a data e o prompt usado, conforme as normas da instituição.",
              ("ABNT. NBR 6023: referências. 2018.", None))

    # Bia: entregue, aguardando a revisão do professor
    como("bia")
    p_bia = pesquisas.criar(projeto.id, "IA generativa e plágio acadêmico",
                            "Medir a percepção de plágio quando se usa IA generativa.")
    _, (b1, b2) = interacao(
        p_bia, "Gemini", "Como detectar texto escrito por IA?",
        "Detectores têm taxa de erro alta e não devem ser a única evidência.",
        ("OLIVEIRA, P. Detectores de texto sintético. Cadernos de Pesquisa, 2024.", "https://exemplo.org/oliveira"),
        ("WEBER, T. Fake or real? Text provenance. ACM, 2023.", None),
    )
    fontes.verificar(b1.id, "verificada", "Confirmado no site da revista.", "Detectores erram com frequência.")
    pesquisas.entregar(p_bia.id)

    # Caio: concluída (entregue, revisada e aceita pela professora)
    como("caio")
    p_caio = pesquisas.criar(projeto.id, "Ética no uso de chatbots",
                             "Levantar os dilemas éticos do uso de chatbots em sala de aula.")
    i_caio, (c1,) = interacao(
        p_caio, "ChatGPT", "Quais dilemas éticos envolvem chatbots na escola?",
        "Privacidade dos dados, autoria e desigualdade de acesso.",
        ("FLORIDI, L. The Ethics of Artificial Intelligence. Oxford University Press, 2023.", "https://exemplo.org/floridi"),
    )
    fontes.verificar(c1.id, "verificada", "Livro real.", "Autoria e privacidade são os dilemas centrais.")
    pesquisas.entregar(p_caio.id)
    como("marina")
    revisoes.comentar_interacao(i_caio.id, "Boa escolha de fonte. Cite também a LGPD na próxima.")
    revisoes.confirmar_interacao(i_caio.id)
    revisoes.aceitar(p_caio.id)

    # Dani: devolvida para ajustes
    como("dani")
    p_dani = pesquisas.criar(projeto.id, "IA e acessibilidade", "Levantar usos de IA por pessoas com deficiência.")
    _, (d1,) = interacao(
        p_dani, "Copilot", "Que ferramentas de IA ajudam pessoas com deficiência visual?",
        "Leitores de tela com descrição automática de imagens, entre outros.",
        ("RAMOS, L. Acessibilidade digital e IA. 2022.", None),
    )
    pesquisas.entregar(p_dani.id)
    como("marina")
    revisoes.julgar_fonte(d1.id, "incorreta", "Não localizei esta obra. Confira a referência com o autor.")
    revisoes.devolver(p_dani.id, "A fonte da interação 1 não existe. Corrija a referência e inclua pelo menos duas fontes verificadas.")

    # Eduardo: duas pesquisas em turmas diferentes
    como("edu")
    p_edu = pesquisas.criar(banco.id, "Normalização de tabelas com apoio de IA", "Comparar sugestões de IA para as formas normais.")
    interacao(p_edu, "ChatGPT", "Explique a terceira forma normal.", "Uma relação está em 3FN se não há dependências transitivas.",
              ("ELMASRI, R. Sistemas de Banco de Dados. Pearson, 2011.", None))
    pesquisas.criar(redes.id, "Roteamento explicado por IA", "Verificar a precisão das explicações de IA sobre BGP.")

    # Ana também tem pesquisa em Banco de Dados
    como("ana")
    pesquisas.criar(banco.id, "Modelagem ER assistida por IA", "Avaliar diagramas ER gerados por IA.")

    # ------------------------------------------------------------ grupos e convites (turma Projeto 1)
    ids = {a: usuarios.repo.buscar_por_email(email(a)).id for a in ALUNOS}

    # Time Alfa: Ana criou, Bia aceitou (pesquisa do grupo existe), Caio recusou, Dani ainda não respondeu
    como("ana")
    alfa = grupos.criar(projeto.id, "Time Alfa", "IA e autoria em trabalhos de grupo",
                        "Investigar como grupos dividem a autoria quando usam IA.")
    grupos.convidar(alfa.id, [ids["bia"], ids["caio"], ids["dani"]])
    como("bia")
    for convite in grupos.convites_pendentes(projeto.id):
        grupos.responder_convite(convite.id, True)
    como("caio")
    for convite in grupos.convites_pendentes(projeto.id):
        grupos.responder_convite(convite.id, False)
    como("bia")
    pesquisa_alfa = grupos.obter(alfa.id).pesquisa
    i_alfa, (g1,) = interacao(
        pesquisa_alfa, "Claude", "Como dividir a autoria quando um grupo usa IA?",
        "Registre quem fez cada prompt e quem revisou cada resposta.",
        ("COPE. Authorship and AI tools. 2023.", "https://exemplo.org/cope"),
    )
    como("ana")
    fontes.verificar(g1.id, "verificada", "Documento oficial do COPE.", "Registramos quem fez cada prompt.")

    # Time Beta: Eduardo criou e ainda espera respostas (a pesquisa só nasce no 1º aceite)
    como("edu")
    beta = grupos.criar(projeto.id, "Time Beta", "IA e avaliação por pares", "Testar IA como apoio à avaliação por pares.")
    grupos.convidar(beta.id, [ids["ana"], ids["dani"]])

    sessao.encerrar()


def main(argumentos):
    try:
        armazenamento.loja()
    except armazenamento.ErroDeConfiguracao as erro:
        print(erro)
        return
    print("Conectado ao Firebase (Firestore).")
    if "--limpar" in argumentos:
        limpar()
        return
    if "--recriar" in argumentos:
        limpar()
    elif ja_existe():
        print("Os dados de exemplo já existem. Use --recriar para apagar e criar de novo.")
        return
    popular()
    print(
        f"""
Dados de exemplo criados. Senha de todos: {SENHA}

Professores
  marina{DOMINIO}  Profa. Marina Lopes   turmas: Projeto 1 (PROJ01, com grupos), Banco de Dados (BANCO1)
  carlos{DOMINIO}  Prof. Carlos Teixeira turma: Redes de Computadores (REDES1)

Alunos (turma Projeto 1: ana, bia, caio, dani, edu)
  ana{DOMINIO}   pesquisa em andamento (fontes verificada, incorreta e pendente), grupo Time Alfa, convite pendente do Time Beta
  bia{DOMINIO}   pesquisa entregue (aguardando revisão), integrante do Time Alfa
  caio{DOMINIO}  pesquisa concluída pela professora (recusou o convite do Time Alfa)
  dani{DOMINIO}  pesquisa devolvida para ajustes, com convites pendentes (Time Alfa e Time Beta)
  edu{DOMINIO}   criador do Time Beta (sem pesquisa de grupo ainda), em 3 turmas
  fabi{DOMINIO}  sem turma: use o código PROJ01 para testar a entrada
"""
    )


if __name__ == "__main__":
    main(sys.argv[1:])
