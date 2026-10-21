from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.database import Base

if TYPE_CHECKING:
    from repository.models.interacao import Interacao
    from repository.models.relatorio import Relatorio
    from repository.models.usuario import Usuario


class Pesquisa(Base):
    __tablename__ = "pesquisa"
    __table_args__ = (
        CheckConstraint("status IN ('em_andamento', 'concluida')", name="ck_pesquisa_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str]
    objetivo: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default="em_andamento")
    data_criacao: Mapped[datetime] = mapped_column(server_default=func.now())
    data_conclusao: Mapped[datetime | None]
    aluno_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"))

    aluno: Mapped["Usuario"] = relationship(back_populates="pesquisas")
    interacoes: Mapped[list["Interacao"]] = relationship(
        back_populates="pesquisa", cascade="all, delete-orphan"
    )
    relatorio: Mapped["Relatorio | None"] = relationship(
        back_populates="pesquisa", cascade="all, delete-orphan", uselist=False
    )
