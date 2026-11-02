from sqlalchemy import select

from repository.database import Session
from repository.models import Usuario


class UsuarioRepository:
    def salvar(self, usuario):
        with Session() as s:
            s.add(usuario)
            s.commit()
        return usuario

    def buscar_por_email(self, email):
        with Session() as s:
            return s.scalars(select(Usuario).where(Usuario.email == email)).first()
