from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.config import settings

# Force SQLite for development to avoid PostgreSQL connection issues
DATABASE_URL = "sqlite:///./focusguard.db"

# Connection arguments (specifically for SQLite check_same_thread requirement)
connect_args = {"check_same_thread": False}

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True  # Detect and recover from stale connections automatically
)

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model class
Base = declarative_base()
