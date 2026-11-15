from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from repository.database import Session
from repository.models import Fonte, Interacao, Pesquisa, Relatorio


class PesquisaRepository:
    def salvar(self, pesquisa):
        with Session() as s:
            s.add(pesquisa)
            s.commit()
        return pesquisa

    def atualizar(self, pesquisa_id, titulo, objetivo):
        """Grava o novo título e objetivo e devolve a pesquisa atualizada."""
        with Session() as s:
            pesquisa = s.get(Pesquisa, pesquisa_id)
            pesquisa.titulo = titulo
            pesquisa.objetivo = objetivo
            s.commit()
            s.refresh(pesquisa)
            return pesquisa

    def buscar_por_id(self, pesquisa_id):
        with Session() as s:
            return s.get(Pesquisa, pesquisa_id)

    def concluir(self, pesquisa_id):
        """RF10: marca a pesquisa como concluída e carimba o relatório, tudo na mesma transação."""
        with Session() as s:
            pesquisa = s.get(Pesquisa, pesquisa_id)
            pesquisa.status = "concluida"
            pesquisa.data_conclusao = func.now()
            relatorio = s.scalars(select(Relatorio).where(Relatorio.pesquisa_id == pesquisa_id)).first()
            if relatorio is None:  # pesquisas antigas, de antes do relatório nascer junto
                relatorio = Relatorio(pesquisa_id=pesquisa_id)
                s.add(relatorio)
            relatorio.data_geracao = func.now()
            s.commit()
            s.refresh(pesquisa)
            return pesquisa

    def listar_concluidas(self):
        """RF23: pesquisas entregues (concluídas), com aluno, interações e fontes carregados,
        da entrega mais recente para a mais antiga."""
        with Session() as s:
            consulta = (
                select(Pesquisa)
                .where(Pesquisa.status == "concluida")
                .options(
                    selectinload(Pesquisa.aluno),
                    selectinload(Pesquisa.interacoes).selectinload(Interacao.fontes),
                )
                .order_by(Pesquisa.data_conclusao.desc(), Pesquisa.id.desc())
            )
            return list(s.scalars(consulta))

    def excluir(self, pesquisa_id):
        """RF09: o cascade do model apaga junto relatório, interações, fontes e trechos."""
        with Session() as s:
            pesquisa = s.get(Pesquisa, pesquisa_id)
            if pesquisa is not None:
                s.delete(pesquisa)
                s.commit()

    def listar_por_aluno(self, aluno_id):
        """Pesquisas do aluno, da mais recente para a mais antiga."""
        with Session() as s:
            consulta = (
                select(Pesquisa)
                .where(Pesquisa.aluno_id == aluno_id)
                .order_by(Pesquisa.data_criacao.desc(), Pesquisa.id.desc())
            )
            return list(s.scalars(consulta))