from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from repository.database import Base


class Turma(Base):
    __tablename__ = "turma"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    professor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"))
