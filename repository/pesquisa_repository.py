from sqlalchemy import select

from repository.database import Session
from repository.models import Pesquisa


class PesquisaRepository:
    def salvar(self, pesquisa):
        with Session() as s:
            s.add(pesquisa)
            s.commit()
        return pesquisa

    def buscar_por_id(self, pesquisa_id):
        with Session() as s:
            return s.get(Pesquisa, pesquisa_id)

    def listar_por_aluno(self, aluno_id):
        """Pesquisas do aluno, da mais recente para a mais antiga."""
        with Session() as s:
            consulta = (
                select(Pesquisa)
                .where(Pesquisa.aluno_id == aluno_id)
                .order_by(Pesquisa.data_criacao.desc(), Pesquisa.id.desc())
            )
            return list(s.scalars(consulta))
