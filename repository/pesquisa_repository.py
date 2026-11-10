from sqlalchemy import select
from sqlalchemy.orm import selectinload

from repository.database import Session
from repository.models import Pesquisa


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

    def listar_todas(self):
        """Todas as pesquisas com o nome do aluno (área do professor), mais recentes primeiro."""
        with Session() as s:
            consulta = (
                select(Pesquisa)
                .options(selectinload(Pesquisa.aluno))
                .order_by(Pesquisa.data_criacao.desc(), Pesquisa.id.desc())
            )
            return list(s.scalars(consulta))

    def listar_por_aluno(self, aluno_id):
        """Pesquisas do aluno, da mais recente para a mais antiga."""
        with Session() as s:
            consulta = (
                select(Pesquisa)
                .where(Pesquisa.aluno_id == aluno_id)
                .order_by(Pesquisa.data_criacao.desc(), Pesquisa.id.desc())
            )
            return list(s.scalars(consulta))