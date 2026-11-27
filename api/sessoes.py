"""Sessões da API: cada login gera um token; cada requisição roda com o usuário daquele token.

Os services guardam o usuário logado numa única sessão global (services.sessao). Para a API
atender vários navegadores, cada requisição pega um cadeado, coloca o usuário do token na sessão
global, roda o service e limpa. É simples e seguro para o uso do projeto (poucos usuários)."""
import secrets
import threading
import time

from services.erros import RegraViolada
from services.sessao import sessao

VALIDADE_SEGUNDOS = 12 * 60 * 60

_cadeado = threading.Lock()
_tokens = {}  # token -> (usuario_id, expira_em)


def criar_token(usuario_id):
    token = secrets.token_urlsafe(32)
    _tokens[token] = (usuario_id, time.time() + VALIDADE_SEGUNDOS)
    return token


def revogar(token):
    _tokens.pop(token, None)


def usuario_id_do_token(token):
    achado = _tokens.get(token)
    if achado is None:
        return None
    usuario_id, expira = achado
    if expira < time.time():
        _tokens.pop(token, None)
        return None
    return usuario_id


def limpar_tudo():
    _tokens.clear()


class Contexto:
    """Usa-se com 'with': trava, loga o usuário do token na sessão global e, ao sair, limpa."""

    def __init__(self, token=None):
        self.token = token

    def __enter__(self):
        _cadeado.acquire()
        try:
            sessao.encerrar()
            if self.token is not None:
                usuario_id = usuario_id_do_token(self.token)
                if usuario_id is None:
                    raise RegraViolada("Sua sessão expirou. Entre de novo.")
                from repository.usuario_repository import UsuarioRepository

                usuario = UsuarioRepository().buscar_por_id(usuario_id)
                if usuario is None:
                    revogar(self.token)
                    raise RegraViolada("Sua sessão expirou. Entre de novo.")
                sessao.iniciar(usuario)
        except BaseException:
            sessao.encerrar()
            _cadeado.release()
            raise
        return sessao.usuario

    def __exit__(self, *_):
        sessao.encerrar()
        _cadeado.release()
        return False
