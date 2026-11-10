from sqlalchemy import select
from sqlalchemy.orm import selectinload

from repository.database import Session
from repository.models import Fonte, Interacao


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

    def buscar_por_id(self, interacao_id):
        """Interação já com as fontes e os trechos de cada fonte (para a tela da interação)."""
        with Session() as s:
            consulta = (
                select(Interacao)
                .where(Interacao.id == interacao_id)
                .options(selectinload(Interacao.fontes).selectinload(Fonte.trechos))
            )
            return s.scalars(consulta).first()

    def atualizar(self, interacao_id, ferramenta_ia, pergunta, resposta):
        """RF13: muda só os textos; as fontes ligadas continuam as mesmas."""
        with Session() as s:
            interacao = s.get(Interacao, interacao_id)
            interacao.ferramenta_ia = ferramenta_ia
            interacao.pergunta = pergunta
            interacao.resposta = resposta
            s.commit()
            return interacao

    def excluir(self, interacao_id):
        """RF14: o cascade do model apaga junto as fontes e os trechos."""
        with Session() as s:
            interacao = s.get(Interacao, interacao_id)
            if interacao is not None:
                s.delete(interacao)
                s.commit()
