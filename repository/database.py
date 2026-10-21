import os
 
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker
 
load_dotenv()
 
url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)
 
engine = create_engine(url)
Session = sessionmaker(engine) 
 
 
class Base(DeclarativeBase):
    """Todas as classes de models.py herdam desta."""
 
