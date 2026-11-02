import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()  # lê o arquivo .env

url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url)

# expire_on_commit=False: depois do commit, o objeto continua legível mesmo com a
# sessão fechada (sem isso, ler usuario.nome dá DetachedInstanceError).
Session = sessionmaker(engine, expire_on_commit=False)  # uso: with Session() as s: ...


class Base(DeclarativeBase):
    """Todas as classes de models/ herdam desta."""
