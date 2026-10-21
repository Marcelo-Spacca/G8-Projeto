from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.database import Base

if TYPE_CHECKING:
    from repository.models.pesquisa import Pesquisa


class Relatorio(Base):
    __tablename__ = "relatorio"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_geracao: Mapped[datetime] = mapped_column(server_default=func.now())
    pesquisa_id: Mapped[int] = mapped_column(
        ForeignKey("pesquisa.id", ondelete="CASCADE"), unique=True  # 1:1 com a pesquisa
    )

    pesquisa: Mapped["Pesquisa"] = relationship(back_populates="relatorio")
