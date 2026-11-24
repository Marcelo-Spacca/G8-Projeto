class RegraViolada(Exception):
    """Levantada quando uma regra do projeto não é cumprida.
    A mensagem já é escrita para o usuário final (a tela só a exibe)."""
