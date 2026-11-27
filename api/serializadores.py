"""Transforma os objetos dos services em dicionários JSON para o front.

Só leitura: nenhuma regra mora aqui. Tudo o que o front mostra já vem calculado (contagens,
rótulos de estado), para a tela não repetir lógica."""
from services.fonte_service import contar_status


def _data(valor):
    return valor.isoformat() if valor else None


def pessoa(u):
    return None if u is None else {"id": u.id, "nome": u.nome, "email": u.email, "tipo": u.tipo}


def _nome(u):
    return None if u is None else {"id": u.id, "nome": u.nome}


def usuario(u):
    return {"id": u.id, "nome": u.nome, "email": u.email, "tipo": u.tipo}


def trecho(t):
    return {"id": t.id, "trecho": t.trecho_citado, "localizacao": t.localizacao}


def fonte(f):
    return {
        "id": f.id,
        "interacao_id": f.interacao_id,
        "referencia": f.referencia,
        "link": f.link,
        "status": f.status,
        "anotacao": f.anotacao_correcao,
        "data_verificacao": _data(f.data_verificacao),
        "julgada_pelo_professor": bool(f.julgada_pelo_professor),
        "trechos": [trecho(t) for t in sorted(f.trechos, key=lambda t: (len(t.id), t.id))],
    }


def contagem(fontes):
    return contar_status(fontes)


def interacao_resumo(i):
    fontes = sorted(i.fontes, key=lambda f: (len(f.id), f.id))
    return {
        "id": i.id,
        "pesquisa_id": i.pesquisa_id,
        "ferramenta": i.ferramenta_ia,
        "pergunta": i.pergunta,
        "data_registro": _data(i.data_registro),
        "confirmada": bool(i.confirmada),
        "tem_comentario": bool(i.comentario_professor),
        "contagem": contagem(fontes),
    }


def interacao(i):
    fontes = sorted(i.fontes, key=lambda f: (len(f.id), f.id))
    return {
        **interacao_resumo(i),
        "resposta": i.resposta,
        "comentario": i.comentario_professor,
        "data_comentario": _data(i.data_comentario),
        "fontes": [fonte(f) for f in fontes],
    }


def grupo(g, com_pesquisa=True):
    membros = g.alunos if g.membros else []
    pendentes = sum(1 for c in (g.convites or []) if c.status == "pendente")
    return {
        "id": g.id,
        "nome": g.nome,
        "titulo": g.titulo,
        "objetivo": g.objetivo,
        "turma_id": g.turma_id,
        "alunos": [_nome(a) for a in membros],
        "convites_pendentes": pendentes,
        "pesquisa": pesquisa(g.pesquisa) if (com_pesquisa and g.pesquisa is not None) else None,
    }


def pesquisa(p, com_interacoes=False):
    interacoes = sorted(p.interacoes or [], key=lambda i: (i.data_registro, len(i.id), i.id))
    fontes = [f for i in interacoes for f in i.fontes]
    dados = {
        "id": p.id,
        "titulo": p.titulo,
        "objetivo": p.objetivo,
        "status": p.status,
        "devolvida": p.devolvida,
        "de_grupo": p.de_grupo,
        "data_criacao": _data(p.data_criacao),
        "data_entrega": _data(p.data_entrega),
        "data_conclusao": _data(p.data_conclusao),
        "data_devolucao": _data(p.data_devolucao),
        "mensagem_devolucao": p.mensagem_devolucao,
        "turma": None if p.turma is None else {"id": p.turma.id, "nome": p.turma.nome},
        "aluno": _nome(p.aluno),
        "grupo": None
        if p.grupo is None
        else {
            "id": p.grupo.id,
            "nome": p.grupo.nome,
            "alunos": [_nome(a) for a in (p.grupo.alunos if p.grupo.membros else [])],
        },
        "n_interacoes": len(interacoes),
        "contagem": contagem(fontes),
    }
    if com_interacoes:
        dados["interacoes"] = [interacao_resumo(i) for i in interacoes]
    return dados


def turma_aluno(t):
    return {
        "id": t.id,
        "nome": t.nome,
        "permite_grupos": bool(t.permite_grupos),
        "professor": None if t.professor is None else t.professor.nome,
    }


def turma_professor(t, completa=False):
    aguardando = sum(1 for p in t.pesquisas if p.status == "entregue")
    dados = {
        "id": t.id,
        "nome": t.nome,
        "codigo": t.codigo,
        "permite_grupos": bool(t.permite_grupos),
        "n_alunos": len(t.matriculas),
        "n_pesquisas": len(t.pesquisas),
        "n_grupos": len(t.grupos),
        "aguardando_revisao": aguardando,
    }
    if completa:
        alunos = t.alunos
        em_grupos = {a.id: [] for a in alunos}
        for g in t.grupos:
            for a in g.alunos:
                em_grupos.setdefault(a.id, []).append(g.nome)
        por_id = {p.id: p for p in t.pesquisas}
        dados["alunos"] = [
            {
                "id": a.id,
                "nome": a.nome,
                "grupos": sorted(em_grupos.get(a.id, [])),
                "pesquisas": [
                    pesquisa(p)
                    for p in sorted(
                        (p for p in t.pesquisas if p.aluno_id == a.id),
                        key=lambda p: (p.data_entrega or p.data_criacao, p.id),
                        reverse=True,
                    )
                ],
            }
            for a in alunos
        ]
        com_grupo = {a.id for g in t.grupos for a in g.alunos}
        dados["sem_grupo"] = [_nome(a) for a in alunos if a.id not in com_grupo]
        dados["grupos"] = []
        for g in sorted(t.grupos, key=lambda g: (g.nome.lower(), g.id)):
            d = grupo(g, com_pesquisa=False)
            if g.pesquisa is not None:
                d["pesquisa"] = pesquisa(por_id.get(g.pesquisa.id, g.pesquisa))
            dados["grupos"].append(d)
        dados["alunos_lista"] = [_nome(a) for a in alunos]
    return dados


def convite(c):
    g = c.grupo
    return {
        "id": c.id,
        "grupo": None if g is None else {"id": g.id, "nome": g.nome},
        "titulo": None if g is None else g.titulo,
        "convidado_por": None if c.convidado_por is None else c.convidado_por.nome,
        "integrantes": [] if g is None or not g.membros else [a.nome for a in g.alunos],
    }


def relatorio(gerado):
    p = gerado.pesquisa
    interacoes = gerado.interacoes
    return {
        "situacao": "concluida" if gerado.concluida else "entregue" if gerado.entregue else "previa",
        "pesquisa": {
            "id": p.id,
            "titulo": p.titulo,
            "objetivo": p.objetivo,
            "status": p.status,
            "data_entrega": _data(p.data_entrega),
            "data_conclusao": _data(p.data_conclusao),
            "turma": None if p.turma is None else p.turma.nome,
            "aluno": None if p.aluno is None else p.aluno.nome,
            "grupo": None
            if p.grupo is None
            else {"nome": p.grupo.nome, "alunos": [a.nome for a in p.grupo.alunos]},
        },
        "contagem": gerado.contagem_status(),
        "n_interacoes": len(interacoes),
        "n_fontes": len(gerado.fontes),
        "interacoes": [interacao(i) for i in interacoes],
    }
