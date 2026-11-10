from sqlalchemy import func, select

from repository.database import Session
from repository.models import Fonte, Interacao, Pesquisa, Relatorio, Usuario
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
        + ["3", "1"]                                                 # abrir a interação nº 1
        + ["0"]                                                      # voltar da interação
        + ["0"]                                                      # voltar da pesquisa
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


def test_professor_sem_pesquisas_e_opcao_invalida():
    texto = rodar(
        ["1", "Profa", "p@x.com", "123456", "2"]
        + ["2", "p@x.com", "123456"]
        + ["1"]                                                      # listar: ainda não há pesquisas
        + ["3"]                                                      # opção de aluno: inválida
        + ["0", "0"]
    )
    assert "1. Listar pesquisas dos alunos" in texto
    assert "Nenhum aluno criou pesquisas ainda." in texto
    assert texto.count("Opção inválida.") == 1


# ---------------------------------------------------------------- RF13, RF14, RF18, RF26, RF27, RF20
ABRIR_PESQUISA_COM_INTERACAO = (
    ["1", "Impacto da IA", "Entender o uso de IA"]
    + ["3", "1"]
    + ["1", "ChatGPT", "Qual o efeito?", "FIM", "Grande.", "FIM"]
)
ABRIR_INTERACAO_1 = ["3", "1"]


def test_fontes_verificacao_trecho_e_anotacao_na_tela_da_interacao():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA + ABRIR_PESQUISA_COM_INTERACAO + ABRIR_INTERACAO_1
        + ["3", "Silva (2023)"]                                      # adicionar fonte 1
        + ["3", "Inventada (2099)"]                                  # adicionar fonte 2
        + ["4", "1", "1", "Confere com o livro", "FIM",              # verificar fonte 1 (RF18)
           "s", "A IA mudou o ensino.", "FIM", "§2"]                 # ... e ligar trecho (RF26)
        + ["4", "2", "2", "O DOI não existe", "FIM"]                 # fonte 2 incorreta
        + ["5", "1", "Outro trecho", "FIM", ""]                      # mais um trecho na fonte 1
        + ["5", "2", "x", "FIM", ""]                                 # trecho em fonte incorreta: erro
        + ["0", "0", "0", "0"]
    )
    assert "Verificação salva." in texto and "Trecho ligado à fonte." in texto
    assert "[ERRO] Só é possível ligar um trecho a uma fonte verificada." in texto
    # RF27: o trecho aparece logo abaixo da sua fonte, antes da próxima fonte
    ultima_tela = texto[texto.rindex("FONTES:"):]
    assert ultima_tela.index("Silva (2023)  [Verificada]") \
        < ultima_tela.index('-> Trecho (§2): "A IA mudou o ensino."') \
        < ultima_tela.index('-> Trecho: "Outro trecho"') \
        < ultima_tela.index("Inventada (2099)  [Incorreta]")
    assert "Anotação: O DOI não existe" in ultima_tela


def test_editar_interacao_pelo_menu_mantem_fontes():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA + ABRIR_PESQUISA_COM_INTERACAO + ABRIR_INTERACAO_1
        + ["3", "Silva (2023)"]
        + ["1", "", "Qual o efeito real?", "FIM", "FIM"]             # muda só a pergunta
        + ["0", "0", "0", "0"]
    )
    assert "Interação atualizada. As fontes ligadas foram mantidas." in texto
    ultima_tela = texto[texto.rindex("Ferramenta: "):]
    assert "PERGUNTA:\nQual o efeito real?" in ultima_tela
    assert "RESPOSTA DA IA:\nGrande." in ultima_tela              # em branco: manteve
    assert "Ferramenta: ChatGPT" in ultima_tela
    assert "Silva (2023)" in ultima_tela
    assert contar(Fonte) == 1


def test_excluir_interacao_pede_confirmacao():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA + ABRIR_PESQUISA_COM_INTERACAO + ABRIR_INTERACAO_1
        + ["3", "Silva (2023)"]
        + ["2", "n"]                                                 # desiste
        + ["2", "s"]                                                 # confirma
        + ["0", "0", "0"]
    )
    assert "Exclusão cancelada." in texto and "Interação excluída." in texto
    assert (contar(Interacao), contar(Fonte)) == (0, 0)


def test_relatorio_pelo_aluno_e_pelo_professor():
    texto = rodar(
        CADASTRAR_ANA + ENTRAR_ANA + ABRIR_PESQUISA_COM_INTERACAO + ABRIR_INTERACAO_1
        + ["3", "Silva (2023)"]
        + ["4", "1", "1", "", "FIM", "s", "Meu texto", "FIM", "§3"]
        + ["0"]                                                      # volta para a pesquisa
        + ["5"]                                                      # relatório (aluno)
        + ["0", "0"]                                                 # volta e sai da conta
        + ["1", "Profa", "p@x.com", "123456", "2"]
        + ["2", "p@x.com", "123456"]
        + ["1"]                                                      # lista pesquisas
        + ["2", "1"]                                                 # relatório da pesquisa nº 1
        + ["0", "0"]
    )
    assert texto.count("RELATÓRIO DE USO DE IA") == 2
    relatorio_professor = texto[texto.rindex("RELATÓRIO DE USO DE IA"):]
    assert "Pesquisa: Impacto da IA" in relatorio_professor
    assert "Aluno: Ana" in relatorio_professor
    assert "1 interação(ões), 1 fonte(s) — 1 verificada(s), 0 incorreta(s), 0 não verificada(s)" in relatorio_professor
    assert "PERGUNTA:\nQual o efeito?" in relatorio_professor
    assert 'Trecho (§3): "Meu texto"' in relatorio_professor
    assert contar(Relatorio) == 1


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