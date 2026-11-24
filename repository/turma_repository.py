from repository import armazenamento
from repository.armazenamento import chave_unica
from repository.carga import carregar_turmas, mais_recentes_primeiro, usuarios_por_id
from repository.cascata import apagar_turmas
from repository.models import Matricula, Turma


def _turma(doc):
    return Turma.de_dict(doc) if doc else None


class TurmaRepository:
    def salvar(self, turma):
        """Grava a turma. O código de entrada é único: o documento 'unicos/codigo-...' é criado no
        mesmo lote e, se o código já existir, a gravação inteira falha com Duplicado."""
        loja = armazenamento.loja()
        turma.id = loja.novo_id()
        lote = loja.lote()
        lote.criar("unicos", chave_unica("codigo", turma.codigo), {"turma_id": turma.id})
        lote.criar("turmas", turma.id, turma.para_dict())
        lote.confirmar()
        return turma

    def codigo_existe(self, codigo):
        return armazenamento.loja().obter("unicos", chave_unica("codigo", codigo)) is not None

    def buscar_por_codigo(self, codigo):
        docs = armazenamento.loja().consultar("turmas", codigo=codigo)
        return _turma(docs[0]) if docs else None

    def buscar_por_id(self, turma_id):
        doc = armazenamento.loja().obter("turmas", turma_id)
        return carregar_turmas([doc], professor=True)[0] if doc else None

    def listar_do_professor(self, professor_id):
        """Turmas do professor, da mais recente para a mais antiga, com matrículas, pesquisas e
        grupos carregados (a lista mostra quantos alunos e quantas pesquisas aguardam revisão)."""
        docs = armazenamento.loja().consultar("turmas", professor_id=professor_id)
        turmas = carregar_turmas(docs, matriculas=True, pesquisas=True, grupos=True)
        return mais_recentes_primeiro(turmas, lambda t: t.data_criacao)

    def carregar_completa(self, turma_id):
        """A turma com alunos, grupos (integrantes e pesquisa) e pesquisas (com interações e fontes)."""
        doc = armazenamento.loja().obter("turmas", turma_id)
        if doc is None:
            return None
        return carregar_turmas([doc], professor=True, matriculas=True, grupos=True, pesquisas=True)[0]

    def excluir(self, turma_id):
        """Apaga a turma e, em cascata, matrículas, grupos, convites, pesquisas, interações,
        fontes e trechos que estavam nela (ver cascata.py)."""
        loja = armazenamento.loja()
        lote = loja.lote()
        apagar_turmas(loja, lote, [turma_id])
        lote.confirmar()

    # ---------------------------------------------------------------- matrícula
    def matricular(self, turma_id, aluno_id):
        """O id da matrícula é 'turma_aluno': matricular duas vezes levanta Duplicado."""
        matricula = Matricula(turma_id=turma_id, aluno_id=aluno_id)
        matricula.id = f"{turma_id}_{aluno_id}"
        armazenamento.loja().criar("matriculas", matricula.id, matricula.para_dict())

    def aluno_esta_na_turma(self, turma_id, aluno_id):
        return armazenamento.loja().obter("matriculas", f"{turma_id}_{aluno_id}") is not None

    def listar_do_aluno(self, aluno_id):
        """As turmas em que o aluno entrou, da matrícula mais recente para a mais antiga."""
        loja = armazenamento.loja()
        matriculas = [Matricula.de_dict(d) for d in loja.consultar("matriculas", aluno_id=aluno_id)]
        turmas = loja.obter_varios("turmas", [m.turma_id for m in matriculas])
        recentes = mais_recentes_primeiro(matriculas, lambda m: m.data_entrada)
        ordem = [m.turma_id for m in recentes if m.turma_id in turmas]
        return carregar_turmas([turmas[i] for i in ordem], professor=True)  # carregar_turmas mantém a ordem

    def listar_alunos(self, turma_id):
        """Alunos matriculados na turma, em ordem alfabética."""
        matriculas = armazenamento.loja().consultar("matriculas", turma_id=turma_id)
        alunos = usuarios_por_id([m["aluno_id"] for m in matriculas]).values()
        return sorted(alunos, key=lambda a: (a.nome.lower(), len(a.id), a.id))
