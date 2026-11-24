from repository import armazenamento
from repository.armazenamento import ErroDeIntegridade, chave_unica
from repository.cascata import apagar_usuario
from repository.models import Usuario

TIPOS = ("aluno", "professor")


class UsuarioRepository:
    def salvar(self, usuario):
        """Grava o usuário. O e-mail é único: o documento 'unicos/email-...' é criado junto, no mesmo
        lote, e se já existir a gravação inteira falha com Duplicado."""
        if usuario.tipo not in TIPOS:
            raise ErroDeIntegridade(f"tipo de usuário inválido: {usuario.tipo!r}")
        loja = armazenamento.loja()
        novo_id = loja.novo_id()
        lote = loja.lote()
        lote.criar("unicos", chave_unica("email", usuario.email), {"usuario_id": novo_id})
        lote.criar("usuarios", novo_id, usuario.para_dict())
        lote.confirmar()
        usuario.id = novo_id
        return usuario

    def buscar_por_email(self, email):
        docs = armazenamento.loja().consultar("usuarios", email=email)
        return Usuario.de_dict(docs[0]) if docs else None

    def buscar_por_id(self, usuario_id):
        doc = armazenamento.loja().obter("usuarios", usuario_id)
        return Usuario.de_dict(doc) if doc else None

    def listar_com_email_terminando_em(self, sufixo):
        """Usado pelo script de dados de exemplo para achar só as contas de exemplo."""
        todos = armazenamento.loja().consultar("usuarios")
        return [Usuario.de_dict(d) for d in todos if d.get("email", "").endswith(sufixo)]

    def excluir(self, usuario_id):
        """Apaga o usuário e o que é dele: pesquisas, matrículas, turmas (se professor)..."""
        loja = armazenamento.loja()
        lote = loja.lote()
        apagar_usuario(loja, lote, usuario_id)
        lote.confirmar()
