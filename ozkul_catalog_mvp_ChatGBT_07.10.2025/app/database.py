import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # fallback to SQLite for local/dev
    DATABASE_URL = "sqlite+pysqlite:///./ozkul.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={} if not DATABASE_URL.startswith("sqlite") else {"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
