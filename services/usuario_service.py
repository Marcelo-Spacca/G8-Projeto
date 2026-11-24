import re

from repository.models import Usuario
from repository.usuario_repository import UsuarioRepository
from services.erros import RegraViolada
from services.seguranca import confere_senha, gerar_hash
from services.sessao import sessao

TIPOS = ("aluno", "professor")
SENHA_MINIMA = 6
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UsuarioService:
    def __init__(self):
        self.repo = UsuarioRepository()

    def cadastrar(self, nome, email, senha, tipo):
        nome = (nome or "").strip()
        email = (email or "").strip().lower()
        senha = senha or ""

        if not nome:
            raise RegraViolada("Informe seu nome.")
        if not _EMAIL.match(email):
            raise RegraViolada("Informe um e-mail válido.")
        if len(senha) < SENHA_MINIMA:
            raise RegraViolada(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres.")
        if tipo not in TIPOS:
            raise RegraViolada("Escolha o perfil: aluno ou professor.")
        if self.repo.buscar_por_email(email):
            raise RegraViolada("Já existe uma conta com este e-mail.")

        usuario = Usuario(nome=nome, email=email, senha_hash=gerar_hash(senha), tipo=tipo)
        return self.repo.salvar(usuario)

    def entrar(self, email, senha):
        email = (email or "").strip().lower()
        usuario = self.repo.buscar_por_email(email)
        # Mesma mensagem para e-mail inexistente e senha errada, de propósito.
        if usuario is None or not confere_senha(senha or "", usuario.senha_hash):
            raise RegraViolada("E-mail ou senha incorretos.")
        sessao.iniciar(usuario)
        return usuario

    def sair(self):
        """RF02 (logout): encerra a sessão."""
        sessao.encerrar()
