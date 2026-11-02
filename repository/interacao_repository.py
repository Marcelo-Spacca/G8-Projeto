from sqlalchemy import select

from repository.database import Session
from repository.models import Interacao


class InteracaoRepository:
    def salvar(self, interacao):
        with Session() as s:
            s.add(interacao)
            s.commit()
        return interacao

    def listar_por_pesquisa(self, pesquisa_id):
        """Interações da pesquisa, em ordem de registro."""
        with Session() as s:
            consulta = (
                select(Interacao)
                .where(Interacao.pesquisa_id == pesquisa_id)
                .order_by(Interacao.data_registro, Interacao.id)
            )
            return list(s.scalars(consulta))
