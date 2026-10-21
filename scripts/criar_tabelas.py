from repository.database import Base, engine
import repository.models  # noqa: F401  (o __init__.py importa os 7 models e os registra em Base)
 
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tabelas criadas:", ", ".join(sorted(Base.metadata.tables)))
 
