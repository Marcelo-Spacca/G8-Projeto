"""Monta o relatório como HTML. O mesmo texto aparece na tela e vai para o PDF.

Só usa o que o Qt entende de HTML (tabelas, cores, negrito), por isso as linhas finas das tabelas
são feitas com 'cellspacing' sobre um fundo cinza e não com bordas CSS.
"""
from html import escape

from ui import estilo
from ui.componentes import STATUS_FONTE, formatar_data, plural


def _texto(valor):
    """Texto do usuário seguro para HTML, mantendo as quebras de linha."""
    return escape(valor or "").replace("\n", "<br>")


def _link(endereco):
    if endereco.lower().startswith(("http://", "https://")):
        return f'<a href="{escape(endereco, quote=True)}" style="color:{estilo.PRIMARIO}">{escape(endereco)}</a>'
    return escape(endereco)


def _celula_status(status):
    texto, tipo = STATUS_FONTE[status]
    cor, fundo = estilo.CORES_STATUS[tipo]
    return f'<td bgcolor="{fundo}" valign="top"><b><span style="color:{cor}">{escape(texto)}</span></b></td>'


def _celula_fonte(fonte):
    partes = [f"<b>{_texto(fonte.referencia)}</b>"]
    if fonte.link:
        partes.append(f"<br>{_link(fonte.link)}")
    if fonte.julgada_pelo_professor:
        partes.append(f'<br><span style="color:{estilo.PRIMARIO}"><b>Julgada pelo professor</b></span>')
    if fonte.anotacao_correcao:
        quem = "professor" if fonte.julgada_pelo_professor else "aluno"
        partes.append(
            f'<br><span style="color:{estilo.MUDO}">Anotação do {quem}: {_texto(fonte.anotacao_correcao)}</span>'
        )
    return f'<td bgcolor="#FFFFFF" valign="top">{"".join(partes)}</td>'


def _celula_trecho(fonte):
    trechos = sorted(fonte.trechos, key=lambda t: t.id)
    if not trechos:
        aviso = "— sem trecho (fonte descartada)" if fonte.status == "incorreta" else "— sem trecho ligado"
        return f'<td bgcolor="#FFFFFF" valign="top"><span style="color:{estilo.MUDO}">{aviso}</span></td>'
    blocos = []
    for t in trechos:
        onde = f' <span style="color:{estilo.MUDO}">({_texto(t.localizacao)})</span>' if t.localizacao else ""
        blocos.append(f"<i>“{_texto(t.trecho_citado)}”</i>{onde}")
    return f'<td bgcolor="#FFFFFF" valign="top">{"<br><br>".join(blocos)}</td>'


def _bloco_resumo(gerado):
    contagem = gerado.contagem_status()
    itens = [
        (plural(len(gerado.interacoes), "interação", "interações"), "#E9EDF3", estilo.TINTA),
        (plural(len(gerado.fontes), "fonte", "fontes"), "#E9EDF3", estilo.TINTA),
        (plural(contagem["verificada"], "verificada", "verificadas"), estilo.VERDE_FUNDO, estilo.VERDE),
        (plural(contagem["incorreta"], "incorreta", "incorretas"), estilo.VERMELHO_FUNDO, estilo.VERMELHO),
        (plural(contagem["nao_verificada"], "não verificada", "não verificadas"), estilo.AMBAR_FUNDO, estilo.AMBAR),
    ]
    celulas = "".join(
        f'<td bgcolor="{fundo}" align="center"><b><span style="color:{cor}">{texto}</span></b></td>'
        for texto, fundo, cor in itens
    )
    return f'<table width="98%" cellspacing="6" cellpadding="8"><tr>{celulas}</tr></table>'


def _comentario(interacao):
    if not interacao.comentario_professor:
        return ""
    return (
        f'<table width="98%" cellspacing="0" cellpadding="8"><tr><td bgcolor="{estilo.AZUL_FUNDO}">'
        f'<b><span style="color:{estilo.PRIMARIO}">Comentário do professor</span></b><br>'
        f"{_texto(interacao.comentario_professor)}</td></tr></table>"
    )


def _bloco_interacao(numero, interacao):
    confirmada = (
        f' <span style="color:{estilo.VERDE}; font-size:11pt">✓ confirmada pelo professor</span>'
        if interacao.confirmada
        else ""
    )
    topo = (
        f'<h3 style="color:{estilo.TINTA}">Interação {numero}: {_texto(interacao.ferramenta_ia)} '
        f'<span style="color:{estilo.MUDO}; font-weight:normal"> {formatar_data(interacao.data_registro)}</span>'
        f"{confirmada}</h3>"
    )
    texto = (
        f'<p><b>Pergunta</b><br>{_texto(interacao.pergunta)}</p>'
        f'<p><b>Resposta da IA</b><br>{_texto(interacao.resposta)}</p>'
    )
    fontes = sorted(interacao.fontes, key=lambda f: f.id)
    if not fontes:
        return topo + texto + f'<p style="color:{estilo.MUDO}">Nenhuma fonte citada nesta interação.</p>' + _comentario(interacao)
    cabecalho = "".join(
        f'<td bgcolor="#E9EDF3" width="{largura}%"><b>{nome}</b></td>'
        for nome, largura in (("Fonte", 38), ("Status", 22), ("Trecho no texto do aluno", 40))
    )
    linhas = "".join(
        f"<tr>{_celula_fonte(f)}{_celula_status(f.status)}{_celula_trecho(f)}</tr>" for f in fontes
    )
    tabela = (
        f'<table width="98%" cellspacing="1" cellpadding="8" bgcolor="{estilo.LINHA}">'
        f"<tr>{cabecalho}</tr>{linhas}</table>"
    )
    return topo + texto + tabela + _comentario(interacao)


def _linhas_de_autoria(p):
    """Turma e quem assina: o aluno, ou o grupo com os integrantes."""
    linhas = []
    if p.turma is not None:
        linhas.append(f"<tr><td><b>Turma</b></td><td>{_texto(p.turma.nome)}</td></tr>")
    if p.de_grupo:
        integrantes = ", ".join(a.nome for a in p.grupo.alunos)
        linhas.append(f"<tr><td><b>Grupo</b></td><td>{_texto(p.grupo.nome)}</td></tr>")
        linhas.append(f"<tr><td><b>Integrantes</b></td><td>{_texto(integrantes)}</td></tr>")
    else:
        linhas.append(f"<tr><td><b>Aluno</b></td><td>{_texto(p.aluno.nome)}</td></tr>")
    return "".join(linhas)


def montar(gerado):
    """HTML completo do relatório (RF20, RF21, RF28). 'gerado' é o RelatorioGerado do service."""
    p = gerado.pesquisa
    if gerado.concluida:
        situacao = f"Concluída: aceita pelo professor em {formatar_data(p.data_conclusao)}"
        cor_situacao = estilo.VERDE
    elif gerado.entregue:
        situacao = f"Entregue em {formatar_data(p.data_entrega)}, aguardando a revisão do professor"
        cor_situacao = estilo.AMBAR
    else:
        situacao = "Prévia: a pesquisa ainda não foi entregue ao professor"
        cor_situacao = estilo.AMBAR
    cabecalho = (
        f'<h1 style="color:{estilo.TINTA}">Relatório de uso de IA</h1>'
        f'<p><b><span style="color:{cor_situacao}">{situacao}</span></b></p>'
        '<table cellspacing="0" cellpadding="3">'
        f"<tr><td><b>Pesquisa</b></td><td>{_texto(p.titulo)}</td></tr>"
        f"{_linhas_de_autoria(p)}"
        f"<tr><td valign='top'><b>Objetivo</b></td><td>{_texto(p.objetivo)}</td></tr>"
        "</table>"
    )
    if gerado.interacoes:
        corpo = "".join(_bloco_interacao(n, i) for n, i in enumerate(gerado.interacoes, 1))
    else:
        corpo = f'<p style="color:{estilo.MUDO}">Nenhuma interação registrada nesta pesquisa.</p>'
    return f"{cabecalho}<br>{_bloco_resumo(gerado)}{corpo}"
