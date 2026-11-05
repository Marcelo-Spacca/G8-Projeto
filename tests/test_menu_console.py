from sqlalchemy import func, select

from repository.database import Session
from repository.models import Interacao, Pesquisa, Usuario
from ui.menu_console import MenuConsole


def rodar(respostas):
    """Executa o menu com as respostas dadas; devolve tudo o que ele escreveu."""
    fila = iter(respostas)
    saida = []

    def proxima(prompt=""):
        try:
            return next(fila)
        except StopIteration:
            raise EOFError  # acabou a entrada, igual a um Ctrl+D

    menu = MenuConsole(entrada=proxima, saida=saida.append, senha=proxima)
    menu.executar()
    assert next(fila, None) is None, "sobraram respostas: o menu terminou antes do esperado"
    return "\n".join(saida)


def contar(modelo):
    with Session() as s:
        return s.scalar(select(func.count()).select_from(modelo))


CADASTRAR_ANA = ["1", "Ana", "ana@x.com", "segredo1", "1"]
ENTRAR_ANA = ["2", "ana@x.com", "segredo1"]


def test_fluxo_completo_do_aluno():
    texto = rodar(
        CADASTRAR_ANA
        + ENTRAR_ANA
        + ["1", "Impacto da IA", "Entender o uso de IA"]            # criar pesquisa
        + ["2"]                                                      # listar pesquisas
        + ["3", "1"]                                                 # abrir a pesquisa nº 1
        + ["1", "ChatGPT", "Qual o efeito da IA?", "FIM", "Efeito grande.", "Segunda linha.", "FIM"]
        + ["2"]                                                      # listar interações
        + ["3", "1"]                                                 # ver a interação nº 1
        + ["0"]                                                      # voltar
        + ["0"]                                                      # sair da conta
        + ["0"]                                                      # sair do programa
    )
    assert "Conta criada: Ana" in texto
    assert "Bem-vindo(a), Ana!" in texto
    assert "Pesquisa criada: Impacto da IA [Em andamento]" in texto
    assert "Interação registrada." in texto
    assert "PERGUNTA:\nQual o efeito da IA?" in texto
    assert "RESPOSTA DA IA:\nEfeito grande.\nSegunda linha." in texto
    assert "Você saiu da conta." in texto and "Até logo!" in texto
    assert (contar(Usuario), contar(Pesquisa), contar(Interacao)) == (1, 1, 1)


def test_erros_de_regra_aparecem_sem_derrubar_o_menu():
    texto = rodar(
        ["1", "", "sem-arroba", "123", "1"]                          # cadastro inválido (nome vazio)
        + CADASTRAR_ANA
        + ["2", "ana@x.com", "errada"]                               # senha errada
        + ["1", "Ana", "ana@x.com", "outrasenha", "1"]               # e-mail repetido
        + ["0"]
    )
    assert "[ERRO] Informe seu nome." in texto
    assert "[ERRO] E-mail ou senha incorretos." in texto
    assert "[ERRO] Já existe uma conta com este e-mail." in texto
    assert contar(Usuario) == 1


def test_opcao_invalida_e_pesquisa_sem_itens():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA
        + ["9"]                                                      # opção inválida
        + ["2"]                                                      # nenhuma pesquisa ainda
        + ["3"]                                                      # abrir sem ter nenhuma
        + ["0", "0"]
    )
    assert texto.count("Opção inválida.") == 1
    assert texto.count("Você ainda não criou nenhuma pesquisa.") == 2


def test_numero_invalido_ao_abrir_pesquisa():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA
        + ["1", "T", "O"]
        + ["3", "7"]                                                 # só existe a nº 1
        + ["0", "0"]
    )
    assert "Número inválido." in texto


def test_interacao_incompleta_mostra_erro_e_nao_grava():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA
        + ["1", "T", "O", "3", "1"]
        + ["1", "", "pergunta", "FIM", "resposta", "FIM"]            # ferramenta vazia
        + ["0", "0", "0"]
    )
    assert "[ERRO] Informe a ferramenta de IA usada." in texto
    assert contar(Interacao) == 0


def test_professor_ve_aviso_e_nao_acessa_pesquisas():
    texto = rodar(
        ["1", "Profa", "p@x.com", "123456", "2"]
        + ["2", "p@x.com", "123456"]
        + ["1"]                                                      # opção de aluno: inválida
        + ["0", "0"]
    )
    assert "A área do professor ainda não foi implementada." in texto
    assert texto.count("Opção inválida.") == 1


def test_fim_da_entrada_encerra_com_educacao():
    texto = rodar([])  # nenhuma resposta: simula Ctrl+D
    assert "Até logo!" in texto


def test_editar_pesquisa_pelo_menu():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA
        + ["1", "Tema antigo", "Objetivo antigo"]                    # criar pesquisa
        + ["3", "1"]                                                 # abrir a pesquisa nº 1
        + ["4", "Tema novo", ""]                                     # editar: novo título, mantém objetivo
        + ["4", "", ""]                                              # editar sem mudar nada
        + ["0", "0", "0"]
    )
    assert "Pesquisa atualizada: Tema novo" in texto
    assert "Pesquisa: Tema novo [Em andamento]" in texto
    assert "Objetivo: Objetivo antigo" in texto
    with Session() as s:
        p = s.scalars(select(Pesquisa)).one()
        assert (p.titulo, p.objetivo) == ("Tema novo", "Objetivo antigo")