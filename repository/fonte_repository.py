from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from repository.database import Session
from repository.models import Fonte, Trecho


class FonteRepository:
    def salvar(self, fonte):
        with Session() as s:
            s.add(fonte)
            s.commit()
        return fonte

    def buscar_por_id(self, fonte_id):
        with Session() as s:
            consulta = (
                select(Fonte)
                .where(Fonte.id == fonte_id)
                .options(selectinload(Fonte.interacao), selectinload(Fonte.trechos))
            )
            return s.scalars(consulta).first()

    def registrar_verificacao(self, fonte_id, status, anotacao, trecho):
        """Grava o resultado da verificação (RF18) e, se houver, o trecho ligado (RF26)
        numa única transação: ou salva tudo, ou nada."""
        with Session() as s:
            fonte = s.get(Fonte, fonte_id)
            fonte.status = status
            fonte.data_verificacao = func.now()
            if anotacao is not None:
                fonte.anotacao_correcao = anotacao
            if trecho is not None:
                fonte.trechos.append(trecho)
            s.commit()

    def adicionar_trecho(self, trecho):
        with Session() as s:
            s.add(trecho)
            s.commit()
        return trecho

    def listar_trechos(self, fonte_id):
        with Session() as s:
            consulta = select(Trecho).where(Trecho.fonte_id == fonte_id).order_by(Trecho.id)
            return list(s.scalars(consulta))
