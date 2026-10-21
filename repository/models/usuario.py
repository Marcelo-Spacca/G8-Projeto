from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from repository.database import Base

if TYPE_CHECKING:
    from repository.models.pesquisa import Pesquisa


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("tipo IN ('aluno', 'professor')", name="ck_usuario_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    senha_hash: Mapped[str]  # nunca a senha em texto puro
    tipo: Mapped[str]  # 'aluno' ou 'professor'
    # aluno pertence a uma turma (opcional: Turma está fora do escopo da PoC)
    turma_id: Mapped[int | None] = mapped_column(
        ForeignKey("turma.id", use_alter=True, name="fk_usuario_turma", ondelete="SET NULL")
    )

    pesquisas: Mapped[list["Pesquisa"]] = relationship(
        back_populates="aluno", cascade="all, delete-orphan"
    )
