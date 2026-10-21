from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.database import Base

if TYPE_CHECKING:
    from repository.models.fonte import Fonte


class Trecho(Base):
    __tablename__ = "trecho"

    id: Mapped[int] = mapped_column(primary_key=True)
    trecho_citado: Mapped[str] = mapped_column(Text)
    localizacao: Mapped[str | None]  # parágrafo/linha, opcional
    fonte_id: Mapped[int] = mapped_column(ForeignKey("fonte.id", ondelete="CASCADE"))

    fonte: Mapped["Fonte"] = relationship(back_populates="trechos")
