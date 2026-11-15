from sqlalchemy import text

from repository.database import Base, engine
import repository.models  # noqa: F401  (o __init__.py importa os 7 models e os registra em Base)

# Colunas que entraram depois da primeira versão das tabelas. O create_all só cria tabelas que
# ainda não existem; ele não acrescenta coluna em tabela antiga. Como não usamos Alembic, estas
# linhas fazem esse ajuste (e podem rodar quantas vezes forem preciso).
COLUNAS_NOVAS = [
    "ALTER TABLE fonte ADD COLUMN IF NOT EXISTS link TEXT",  # RF15
]


def criar_tabelas():
    Base.metadata.create_all(engine)
    with engine.begin() as conexao:
        for comando in COLUNAS_NOVAS:
            conexao.execute(text(comando))


if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas criadas/atualizadas:", ", ".join(sorted(Base.metadata.tables)))
