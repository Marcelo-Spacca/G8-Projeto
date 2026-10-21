from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.database import Base

if TYPE_CHECKING:
    from repository.models.interacao import Interacao
    from repository.models.trecho import Trecho


class Fonte(Base):
    __tablename__ = "fonte"
    __table_args__ = (
        CheckConstraint(
            "status IN ('nao_verificada', 'verificada', 'incorreta')", name="ck_fonte_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    referencia: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default="nao_verificada")
    anotacao_correcao: Mapped[str | None] = mapped_column(Text)
    data_verificacao: Mapped[datetime | None]
    interacao_id: Mapped[int] = mapped_column(ForeignKey("interacao.id", ondelete="CASCADE"))

    interacao: Mapped["Interacao"] = relationship(back_populates="fontes")
    trechos: Mapped[list["Trecho"]] = relationship(
        back_populates="fonte", cascade="all, delete-orphan"
    )
