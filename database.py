"""
Database Configuration and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database URL - Update with your PostgreSQL credentials
DATABASE_URL = "postgresql://postgres:admin123@localhost:5432/cloud_cost"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Call this once to set up the database schema
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


def drop_all_tables():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)
    print("WARNING: All tables dropped")


def reset_db():
    """
    Reset database - drop and recreate all tables
    USE WITH CAUTION - This will delete all data!
    """
    drop_all_tables()
    init_db()
    print("Database reset complete")

# Made with Bob
