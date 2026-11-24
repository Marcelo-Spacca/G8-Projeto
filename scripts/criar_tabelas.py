from sqlalchemy import text

from repository.database import Base, engine
import repository.models  # noqa: F401  (o __init__.py importa os models e os registra em Base)

# Colunas que entraram depois da primeira versão das tabelas. O create_all só cria tabelas que
# ainda não existem; ele não acrescenta coluna em tabela antiga. Como não usamos Alembic, estas
# linhas fazem esse ajuste (e podem rodar quantas vezes forem preciso).
COLUNAS_NOVAS = [
    "ALTER TABLE fonte ADD COLUMN IF NOT EXISTS link TEXT",  # RF15
    # entrega ao professor, aceitar/devolver
    "ALTER TABLE pesquisa ADD COLUMN IF NOT EXISTS data_entrega TIMESTAMP",
    "ALTER TABLE pesquisa ADD COLUMN IF NOT EXISTS mensagem_devolucao TEXT",
    "ALTER TABLE pesquisa ADD COLUMN IF NOT EXISTS data_devolucao TIMESTAMP",
    # o status ganhou o valor 'entregue': a regra antiga precisa ser trocada
    "ALTER TABLE pesquisa DROP CONSTRAINT IF EXISTS ck_pesquisa_status",
    "ALTER TABLE pesquisa ADD CONSTRAINT ck_pesquisa_status "
    "CHECK (status IN ('em_andamento', 'entregue', 'concluida'))",
    # revisão do professor
    "ALTER TABLE interacao ADD COLUMN IF NOT EXISTS comentario_professor TEXT",
    "ALTER TABLE interacao ADD COLUMN IF NOT EXISTS data_comentario TIMESTAMP",
    "ALTER TABLE interacao ADD COLUMN IF NOT EXISTS confirmada BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE fonte ADD COLUMN IF NOT EXISTS julgada_pelo_professor BOOLEAN NOT NULL DEFAULT FALSE",
    # turmas: código de entrada e permissão de grupos (as tabelas matricula, grupo, grupo_aluno e
    # convite_grupo são novas e o create_all já cria)
    "ALTER TABLE turma ADD COLUMN IF NOT EXISTS codigo VARCHAR(12)",
    "ALTER TABLE turma ADD COLUMN IF NOT EXISTS permite_grupos BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE turma ADD COLUMN IF NOT EXISTS data_criacao TIMESTAMP NOT NULL DEFAULT now()",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_turma_codigo ON turma (codigo)",
    "ALTER TABLE usuario DROP COLUMN IF EXISTS turma_id",  # a ligação agora é a tabela matricula
    # pesquisa ligada a uma turma e, quando for de grupo, ao grupo (sem aluno)
    "ALTER TABLE pesquisa ADD COLUMN IF NOT EXISTS turma_id INTEGER REFERENCES turma(id) ON DELETE CASCADE",
    "ALTER TABLE pesquisa ADD COLUMN IF NOT EXISTS grupo_id INTEGER UNIQUE REFERENCES grupo(id) ON DELETE CASCADE",
    "ALTER TABLE pesquisa ALTER COLUMN aluno_id DROP NOT NULL",
    "ALTER TABLE pesquisa DROP CONSTRAINT IF EXISTS ck_pesquisa_dono",
    "ALTER TABLE pesquisa ADD CONSTRAINT ck_pesquisa_dono CHECK ((aluno_id IS NULL) <> (grupo_id IS NULL))",
]


def criar_tabelas():
    Base.metadata.create_all(engine)
    with engine.begin() as conexao:
        for comando in COLUNAS_NOVAS:
            conexao.execute(text(comando))


if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas criadas/atualizadas:", ", ".join(sorted(Base.metadata.tables)))
