from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# -----------------------------------------------
# DATABASE URL
# -----------------------------------------------
DATABASE_URL = "sqlite:///dermaskin.db"

# -----------------------------------------------
# ENGINE
# -----------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}   # Required for SQLite with FastAPI
)

# -----------------------------------------------
# SESSION LOCAL
# -----------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------------------------
# BASE CLASS (SQLAlchemy 1.4 style)
# -----------------------------------------------
Base = declarative_base()

# -----------------------------------------------
# DEPENDENCY FOR FASTAPI
# -----------------------------------------------
def get_db():
    """Provides a working DB session for routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------
# RAW SQLITE CONNECTION (Legacy Support)
# -----------------------------------------------
def get_connection():
    """Legacy support — returns raw sqlite connection for old code."""
    import sqlite3
    conn = sqlite3.connect("dermaskin.db")
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------------------------
# INITIALIZE DATABASE TABLES
# -----------------------------------------------
def init_db():
    from . import db_models  # imported to register models
    Base.metadata.create_all(bind=engine)
