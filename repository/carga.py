"""Monta os objetos que as telas e os services esperam, com os objetos ligados já carregados
(aluno, turma, grupo e integrantes, interações, fontes, trechos...).

O SQLAlchemy fazia isso com `selectinload`; no Firestore não há JOIN, então cada nível vira uma
consulta própria (feita para a lista inteira de uma vez, não uma por item)."""
from repository import armazenamento
from repository.models import ConviteGrupo, Fonte, Grupo, GrupoAluno, Interacao, Pesquisa, Trecho, Turma, Usuario
from repository.models import Matricula


def chave_id(objeto):
    """Desempate estável: ids mais novos são 'maiores' (comprimento primeiro, depois o texto)."""
    return (len(objeto.id), objeto.id)


def mais_recentes_primeiro(objetos, data):
    """Ordena do mais novo para o mais antigo pela data e, empatando, pelo id."""
    return sorted(objetos, key=lambda o: (data(o), chave_id(o)), reverse=True)


def _agrupar(objetos, atributo):
    grupos = {}
    for objeto in objetos:
        grupos.setdefault(getattr(objeto, atributo), []).append(objeto)
    return grupos


def usuarios_por_id(ids):
    docs = armazenamento.loja().obter_varios("usuarios", ids)
    return {i: Usuario.de_dict(d) for i, d in docs.items()}


def carregar_interacoes(docs, fontes=False, trechos=False):
    loja = armazenamento.loja()
    interacoes = [Interacao.de_dict(d) for d in docs]
    if fontes:
        todas = [Fonte.de_dict(d) for d in loja.consultar_em("fontes", "interacao_id", [i.id for i in interacoes])]
        if trechos:
            por_fonte = _agrupar(
                [Trecho.de_dict(d) for d in loja.consultar_em("trechos", "fonte_id", [f.id for f in todas])],
                "fonte_id",
            )
            for fonte in todas:
                fonte.trechos = sorted(por_fonte.get(fonte.id, []), key=chave_id)
                for trecho in fonte.trechos:
                    trecho.fonte = fonte
        por_interacao = _agrupar(todas, "interacao_id")
        for interacao in interacoes:
            interacao.fontes = sorted(por_interacao.get(interacao.id, []), key=chave_id)
            for fonte in interacao.fontes:
                fonte.interacao = interacao
    return interacoes


def carregar_grupos(docs, turma=False, pesquisa=False, convites=False):
    """Grupos com os integrantes (e o aluno de cada um) sempre; o resto sob pedido."""
    loja = armazenamento.loja()
    grupos = [Grupo.de_dict(d) for d in docs]
    ids = [g.id for g in grupos]
    membros = [GrupoAluno.de_dict(d) for d in loja.consultar_em("grupo_alunos", "grupo_id", ids)]
    convs = [ConviteGrupo.de_dict(d) for d in loja.consultar_em("convites", "grupo_id", ids)] if convites else []
    alunos = usuarios_por_id([m.aluno_id for m in membros] + [c.aluno_id for c in convs])
    for membro in membros:
        membro.aluno = alunos.get(membro.aluno_id)
    for convite in convs:
        convite.aluno = alunos.get(convite.aluno_id)
    membros_por_grupo, convites_por_grupo = _agrupar(membros, "grupo_id"), _agrupar(convs, "grupo_id")
    pesquisas = {}
    if pesquisa:
        achadas = carregar_pesquisas(loja.consultar_em("pesquisas", "grupo_id", ids), interacoes=True, fontes=True)
        pesquisas = {p.grupo_id: p for p in achadas}
    turmas = (
        {i: Turma.de_dict(d) for i, d in loja.obter_varios("turmas", [g.turma_id for g in grupos]).items()}
        if turma
        else {}
    )
    for grupo in grupos:
        grupo.membros = sorted(membros_por_grupo.get(grupo.id, []), key=chave_id)
        for membro in grupo.membros:
            membro.grupo = grupo
        grupo.convites = sorted(convites_por_grupo.get(grupo.id, []), key=chave_id)
        grupo.pesquisa = pesquisas.get(grupo.id)
        if grupo.pesquisa is not None:
            grupo.pesquisa.grupo = grupo
        grupo.turma = turmas.get(grupo.turma_id)
    return grupos


def carregar_pesquisas(
    docs, aluno=False, turma=False, grupo=False, interacoes=False, fontes=False, trechos=False
):
    """Pesquisas com o que for pedido. `grupo` traz o grupo com integrantes e seus alunos."""
    loja = armazenamento.loja()
    pesquisas = [Pesquisa.de_dict(d) for d in docs]
    if aluno:
        alunos = usuarios_por_id([p.aluno_id for p in pesquisas])
        for p in pesquisas:
            p.aluno = alunos.get(p.aluno_id)
    if turma:
        turmas = {i: Turma.de_dict(d) for i, d in loja.obter_varios("turmas", [p.turma_id for p in pesquisas]).items()}
        for p in pesquisas:
            p.turma = turmas.get(p.turma_id)
    if grupo:
        docs_grupos = list(loja.obter_varios("grupos", [p.grupo_id for p in pesquisas]).values())
        grupos = {g.id: g for g in carregar_grupos(docs_grupos)}
        for p in pesquisas:
            p.grupo = grupos.get(p.grupo_id)
    if interacoes:
        todas = carregar_interacoes(
            loja.consultar_em("interacoes", "pesquisa_id", [p.id for p in pesquisas]), fontes=fontes, trechos=trechos
        )
        por_pesquisa = _agrupar(todas, "pesquisa_id")
        for p in pesquisas:
            p.interacoes = sorted(por_pesquisa.get(p.id, []), key=lambda i: (i.data_registro, chave_id(i)))
            for interacao in p.interacoes:
                interacao.pesquisa = p
    return pesquisas


def carregar_turmas(docs, professor=False, matriculas=False, grupos=False, pesquisas=False):
    """Turmas. matriculas -> com o aluno de cada uma; grupos -> com integrantes e pesquisa;
    pesquisas -> com aluno, grupo, interações e fontes."""
    loja = armazenamento.loja()
    turmas = [Turma.de_dict(d) for d in docs]
    ids = [t.id for t in turmas]
    if professor:
        profs = usuarios_por_id([t.professor_id for t in turmas])
        for t in turmas:
            t.professor = profs.get(t.professor_id)
    if matriculas:
        todas = [Matricula.de_dict(d) for d in loja.consultar_em("matriculas", "turma_id", ids)]
        alunos = usuarios_por_id([m.aluno_id for m in todas])
        por_turma = _agrupar(todas, "turma_id")
        for m in todas:
            m.aluno = alunos.get(m.aluno_id)
        for t in turmas:
            t.matriculas = sorted(por_turma.get(t.id, []), key=chave_id)
            for m in t.matriculas:
                m.turma = t
    if grupos:
        todos = carregar_grupos(loja.consultar_em("grupos", "turma_id", ids), pesquisa=True)
        por_turma = _agrupar(todos, "turma_id")
        for t in turmas:
            t.grupos = sorted(por_turma.get(t.id, []), key=chave_id)
            for g in t.grupos:
                g.turma = t
    if pesquisas:
        todas = carregar_pesquisas(
            loja.consultar_em("pesquisas", "turma_id", ids), aluno=True, grupo=True, interacoes=True, fontes=True
        )
        por_turma = _agrupar(todas, "turma_id")
        for t in turmas:
            t.pesquisas = sorted(por_turma.get(t.id, []), key=chave_id)
            for p in t.pesquisas:
                p.turma = t
    return turmas
