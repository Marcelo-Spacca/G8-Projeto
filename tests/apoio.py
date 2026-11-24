"""Ajudas dos testes que olham direto para os dados guardados (no lugar do SQL de antes)."""
from repository import armazenamento


def contar(colecao):
    """Quantos documentos há na coleção ('pesquisas', 'fontes', 'trechos', 'relatorios'...)."""
    return len(armazenamento.loja().consultar(colecao))


def todos(colecao):
    return armazenamento.loja().consultar(colecao)


def definir_status_das_pesquisas(status, pesquisa_id=None):
    """Força o status de uma pesquisa (ou de todas), sem passar pelas regras do service."""
    loja = armazenamento.loja()
    for doc in loja.consultar("pesquisas"):
        if pesquisa_id is None or doc["id"] == str(pesquisa_id):
            loja.atualizar("pesquisas", doc["id"], {"status": status})


def criar_turma_direto(nome, codigo, professor_id, permite_grupos=False):
    """Cria uma turma sem passar pelo TurmaService (para o professor não precisar estar logado)."""
    from repository.models import Turma
    from repository.turma_repository import TurmaRepository

    return TurmaRepository().salvar(
        Turma(nome=nome, codigo=codigo, permite_grupos=permite_grupos, professor_id=professor_id)
    )


def usuario_id(email):
    docs = armazenamento.loja().consultar("usuarios", email=email)
    return docs[0]["id"] if docs else None


def passar_turmas_para(email, codigo=None):
    """Entrega ao professor deste e-mail a turma de código `codigo` (ou todas as turmas)."""
    loja = armazenamento.loja()
    dono = usuario_id(email)
    for turma in loja.consultar("turmas"):
        if codigo is None or turma["codigo"] == codigo:
            loja.atualizar("turmas", turma["id"], {"professor_id": dono})


def turma_do_dono_escondido(nome, codigo, permite_grupos=False, professor_email="prof@x.com"):
    """Cria a turma direto nos dados. Fica com a professora `professor_email`, se ela já existir,
    ou com um dono escondido (dono@x.com) até a professora aparecer."""
    from repository.models import Usuario
    from repository.usuario_repository import UsuarioRepository

    dono = usuario_id(professor_email) or usuario_id("dono@x.com")
    if dono is None:
        dono = UsuarioRepository().salvar(
            Usuario(nome="Dono", email="dono@x.com", senha_hash="x", tipo="professor")
        ).id
    return criar_turma_direto(nome, codigo, dono, permite_grupos).id
