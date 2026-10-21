from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.database import Base

if TYPE_CHECKING:
    from repository.models.fonte import Fonte
    from repository.models.pesquisa import Pesquisa


class Interacao(Base):
    __tablename__ = "interacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    ferramenta_ia: Mapped[str]
    pergunta: Mapped[str] = mapped_column(Text)
    resposta: Mapped[str] = mapped_column(Text)
    data_registro: Mapped[datetime] = mapped_column(server_default=func.now())
    pesquisa_id: Mapped[int] = mapped_column(ForeignKey("pesquisa.id", ondelete="CASCADE"))

    pesquisa: Mapped["Pesquisa"] = relationship(back_populates="interacoes")
    fontes: Mapped[list["Fonte"]] = relationship(
        back_populates="interacao", cascade="all, delete-orphan"
    )
