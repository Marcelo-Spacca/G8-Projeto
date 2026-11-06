"""Consultas ao banco. Não conhecem regra de negócio: só leem e gravam."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from repository.models import Fonte, Interacao, Pesquisa, Relatorio, Trecho, Usuario


class UsuarioRepository:
    def __init__(self, session: Session):
        self.s = session

    def por_email(self, email: str) -> Usuario | None:
        return self.s.scalar(select(Usuario).where(Usuario.email == email))

    def por_id(self, usuario_id: int) -> Usuario | None:
        return self.s.get(Usuario, usuario_id)

    def salvar(self, usuario: Usuario) -> Usuario:
        self.s.add(usuario)
        self.s.flush()
        return usuario


class PesquisaRepository:
    def __init__(self, session: Session):
        self.s = session

    def por_id(self, pesquisa_id: int) -> Pesquisa | None:
        return self.s.get(Pesquisa, pesquisa_id)

    def do_aluno(self, aluno_id: int) -> list[Pesquisa]:
        return list(
            self.s.scalars(
                select(Pesquisa).where(Pesquisa.aluno_id == aluno_id).order_by(Pesquisa.id)
            )
        )

    def todas(self) -> list[Pesquisa]:
        return list(
            self.s.scalars(
                select(Pesquisa).options(selectinload(Pesquisa.aluno)).order_by(Pesquisa.id)
            )
        )

    def completa(self, pesquisa_id: int) -> Pesquisa | None:
        """Pesquisa já carregada com interações, fontes e trechos (para o relatório)."""
        return self.s.scalar(
            select(Pesquisa)
            .where(Pesquisa.id == pesquisa_id)
            .options(
                selectinload(Pesquisa.aluno),
                selectinload(Pesquisa.relatorio),
                selectinload(Pesquisa.interacoes)
                .selectinload(Interacao.fontes)
                .selectinload(Fonte.trechos),
            )
        )

    def salvar(self, pesquisa: Pesquisa) -> Pesquisa:
        self.s.add(pesquisa)
        self.s.flush()
        return pesquisa


class InteracaoRepository:
    def __init__(self, session: Session):
        self.s = session

    def por_id(self, interacao_id: int) -> Interacao | None:
        return self.s.scalar(
            select(Interacao)
            .where(Interacao.id == interacao_id)
            .options(
                selectinload(Interacao.pesquisa),
                selectinload(Interacao.fontes).selectinload(Fonte.trechos),
            )
        )

    def da_pesquisa(self, pesquisa_id: int) -> list[Interacao]:
        return list(
            self.s.scalars(
                select(Interacao)
                .where(Interacao.pesquisa_id == pesquisa_id)
                .options(selectinload(Interacao.fontes))
                .order_by(Interacao.id)
            )
        )

    def salvar(self, interacao: Interacao) -> Interacao:
        self.s.add(interacao)
        self.s.flush()
        return interacao

    def excluir(self, interacao: Interacao) -> None:
        # cascade "all, delete-orphan" remove fontes e trechos junto
        self.s.delete(interacao)
        self.s.flush()


class FonteRepository:
    def __init__(self, session: Session):
        self.s = session

    def por_id(self, fonte_id: int) -> Fonte | None:
        return self.s.scalar(
            select(Fonte)
            .where(Fonte.id == fonte_id)
            .options(
                selectinload(Fonte.interacao).selectinload(Interacao.pesquisa),
                selectinload(Fonte.trechos),
            )
        )

    def salvar(self, fonte: Fonte) -> Fonte:
        self.s.add(fonte)
        self.s.flush()
        return fonte

    def adicionar_trecho(self, trecho: Trecho) -> Trecho:
        self.s.add(trecho)
        self.s.flush()
        return trecho


class RelatorioRepository:
    def __init__(self, session: Session):
        self.s = session

    def da_pesquisa(self, pesquisa_id: int) -> Relatorio | None:
        return self.s.scalar(select(Relatorio).where(Relatorio.pesquisa_id == pesquisa_id))

    def salvar(self, relatorio: Relatorio) -> Relatorio:
        self.s.add(relatorio)
        self.s.flush()
        return relatorio
