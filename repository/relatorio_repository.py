from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from repository.database import Session
from repository.models import Fonte, Interacao, Pesquisa, Relatorio


class RelatorioRepository:
    def buscar_por_pesquisa(self, pesquisa_id):
        with Session() as s:
            return s.scalars(select(Relatorio).where(Relatorio.pesquisa_id == pesquisa_id)).first()

    def registrar_geracao(self, pesquisa_id):
        """RF22: usa o relatório da pesquisa (cria se ainda não existir) e marca a hora de geração."""
        with Session() as s:
            relatorio = s.scalars(
                select(Relatorio).where(Relatorio.pesquisa_id == pesquisa_id)
            ).first()
            if relatorio is None:
                relatorio = Relatorio(pesquisa_id=pesquisa_id)
                s.add(relatorio)
            relatorio.data_geracao = func.now()
            s.commit()
            s.refresh(relatorio)
            return relatorio

    def dados_da_pesquisa(self, pesquisa_id):
        """Pesquisa com aluno, interações, fontes e trechos já carregados (RF20)."""
        with Session() as s:
            consulta = (
                select(Pesquisa)
                .where(Pesquisa.id == pesquisa_id)
                .options(
                    selectinload(Pesquisa.aluno),
                    selectinload(Pesquisa.interacoes)
                    .selectinload(Interacao.fontes)
                    .selectinload(Fonte.trechos),
                )
            )
            return s.scalars(consulta).first()
