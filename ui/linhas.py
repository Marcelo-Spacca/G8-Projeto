"""Linha de pesquisa usada pelas telas do professor (lista geral e telas da turma)."""
from PySide6.QtWidgets import QVBoxLayout

from ui import componentes as c


def resumo_das_fontes(contagem):
    """'3 fontes (1 verificada, 1 incorreta, 1 pendente)' para o professor ver o andamento."""
    total = sum(contagem.values())
    if total == 0:
        return "sem fontes"
    partes = []
    if contagem["verificada"]:
        partes.append(c.plural(contagem["verificada"], "verificada", "verificadas"))
    if contagem["incorreta"]:
        partes.append(c.plural(contagem["incorreta"], "incorreta", "incorretas"))
    if contagem["nao_verificada"]:
        partes.append(c.plural(contagem["nao_verificada"], "pendente", "pendentes"))
    return f"{c.plural(total, 'fonte', 'fontes')} ({', '.join(partes)})"


def linha_de_pesquisa(janela, pesquisa, voltar_texto, voltar_acao, mostrar_autor=True, mostrar_turma=False):
    """Linha clicável de uma pesquisa para o professor: título, quem fez, andamento, "cheque" de
    entrega, data e o botão do relatório (cinza até o aluno entregar). Clicar abre a revisão."""
    entregue = pesquisa.status in ("entregue", "concluida")
    contagem = janela.revisoes.contagem_fontes(pesquisa)
    linha = c.Linha(clicavel=True)
    linha.pesquisa_id = pesquisa.id

    # esquerda: título, autor e o que já foi feito
    esquerda = QVBoxLayout()
    esquerda.setSpacing(4)
    linha.selo = c.selo_da_pesquisa(pesquisa, "professor")
    esquerda.addLayout(c.linha_horizontal(c.rotulo(c.cortar(pesquisa.titulo, 80), "item", quebra=False), linha.selo, None, espaco=10))
    partes = []
    if mostrar_autor:
        partes.append(c.autor_da_pesquisa(pesquisa))
    if mostrar_turma and pesquisa.turma is not None:
        partes.append(pesquisa.turma.nome)
    partes.append(f"{c.plural(len(pesquisa.interacoes), 'interação', 'interações')} • {resumo_das_fontes(contagem)}")
    linha.resumo = c.rotulo("  ·  ".join(partes), "mudo")
    esquerda.addWidget(linha.resumo)

    # meio: o "cheque" de entrega e a data
    meio = QVBoxLayout()
    meio.setSpacing(3)
    linha.caixa = c.CaixaDeEntrega("Entregue para verificação", entregue)
    meio.addWidget(linha.caixa)
    if pesquisa.status == "concluida":
        quando = f"Concluída em {c.formatar_data(pesquisa.data_conclusao)}"
    elif pesquisa.status == "entregue":
        quando = f"Entregue em {c.formatar_data(pesquisa.data_entrega)}"
    elif pesquisa.devolvida:
        quando = f"Devolvida em {c.formatar_dia(pesquisa.data_devolucao)}"
    else:
        quando = "Ainda com o aluno" if not pesquisa.de_grupo else "Ainda com o grupo"
    linha.data = c.rotulo(quando, "dica", quebra=False)
    meio.addWidget(linha.data)

    # direita: o relatório, que só abre depois da entrega
    linha.botao_relatorio = c.botao(
        "Relatório", ao_clicar=lambda pid=pesquisa.id: janela.abrir_relatorio(pid, voltar_texto, voltar_acao)
    )
    linha.botao_relatorio.setEnabled(entregue)
    if not entregue:
        linha.botao_relatorio.setToolTip("O relatório fica disponível quando a pesquisa for entregue.")

    conteudo = c.linha_horizontal(margens=(20, 14, 20, 14), espaco=20)
    conteudo.addLayout(esquerda, 1)
    conteudo.addLayout(meio)
    conteudo.addWidget(linha.botao_relatorio)
    linha.setLayout(conteudo)
    linha.clicado.connect(lambda pid=pesquisa.id: janela.abrir_revisao(pid))
    return linha
