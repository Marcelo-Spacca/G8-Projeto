"""Apagar em cascata.

O Firestore não apaga sozinho o que depende de um documento (o SQL fazia isso com ON DELETE
CASCADE). Aqui cada função junta, num lote, a exclusão do item e de tudo que está embaixo dele:

    turma -> matrículas, grupos, pesquisas
    grupo -> integrantes, convites, a pesquisa do grupo
    pesquisa -> relatório, interações
    interação -> fontes -> trechos

Quem chama faz `lote.confirmar()` no fim. Passando de 500 operações o lote é gravado em pedaços
(ver armazenamento.py): nesse caso específico a exclusão deixa de ser "tudo ou nada".
"""
from repository.armazenamento import chave_unica


def _ids(documentos):
    return [d["id"] for d in documentos]


def apagar_interacoes(loja, lote, interacao_ids):
    interacao_ids = list(interacao_ids)
    fontes = loja.consultar_em("fontes", "interacao_id", interacao_ids)
    for trecho in loja.consultar_em("trechos", "fonte_id", _ids(fontes)):
        lote.apagar("trechos", trecho["id"])
    for fonte_id in _ids(fontes):
        lote.apagar("fontes", fonte_id)
    for interacao_id in interacao_ids:
        lote.apagar("interacoes", interacao_id)


def apagar_pesquisas(loja, lote, pesquisa_ids):
    pesquisa_ids = list(pesquisa_ids)
    interacoes = loja.consultar_em("interacoes", "pesquisa_id", pesquisa_ids)
    apagar_interacoes(loja, lote, _ids(interacoes))
    for pesquisa_id in pesquisa_ids:
        lote.apagar("relatorios", pesquisa_id)  # o id do relatório é o da pesquisa
        lote.apagar("pesquisas", pesquisa_id)


def apagar_grupos(loja, lote, grupo_ids, com_pesquisas=True):
    grupo_ids = list(grupo_ids)
    for membro in loja.consultar_em("grupo_alunos", "grupo_id", grupo_ids):
        lote.apagar("grupo_alunos", membro["id"])
    for convite in loja.consultar_em("convites", "grupo_id", grupo_ids):
        lote.apagar("convites", convite["id"])
    if com_pesquisas:
        apagar_pesquisas(loja, lote, _ids(loja.consultar_em("pesquisas", "grupo_id", grupo_ids)))
    for grupo_id in grupo_ids:
        lote.apagar("grupos", grupo_id)


def apagar_turmas(loja, lote, turma_ids):
    turma_ids = list(turma_ids)
    for matricula in loja.consultar_em("matriculas", "turma_id", turma_ids):
        lote.apagar("matriculas", matricula["id"])
    # as pesquisas dos grupos também têm turma_id, então basta apagar as pesquisas por turma
    apagar_grupos(loja, lote, _ids(loja.consultar_em("grupos", "turma_id", turma_ids)), com_pesquisas=False)
    apagar_pesquisas(loja, lote, _ids(loja.consultar_em("pesquisas", "turma_id", turma_ids)))
    for turma in loja.obter_varios("turmas", turma_ids).values():
        lote.apagar("unicos", chave_unica("codigo", turma["codigo"]))  # o código volta a ficar livre
        lote.apagar("turmas", turma["id"])


def apagar_usuario(loja, lote, usuario_id):
    usuario = loja.obter("usuarios", usuario_id)
    if usuario is None:
        return
    apagar_pesquisas(loja, lote, _ids(loja.consultar("pesquisas", aluno_id=usuario_id)))
    for colecao in ("matriculas", "grupo_alunos", "convites"):
        for doc in loja.consultar(colecao, aluno_id=usuario_id):
            lote.apagar(colecao, doc["id"])
    for convite in loja.consultar("convites", convidado_por_id=usuario_id):
        lote.atualizar("convites", convite["id"], {"convidado_por_id": None})
    for grupo in loja.consultar("grupos", criador_id=usuario_id):
        lote.atualizar("grupos", grupo["id"], {"criador_id": None})
    apagar_turmas(loja, lote, _ids(loja.consultar("turmas", professor_id=usuario_id)))
    lote.apagar("unicos", chave_unica("email", usuario["email"]))
    lote.apagar("usuarios", usuario_id)
