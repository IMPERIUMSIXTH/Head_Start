"""
Database Connection and Utilities
SQLAlchemy setup with PostgreSQL and pgvector support

Author: HeadStart Development Team
Created: 2025-09-05
Purpose: Database connection management, session handling, and base model definitions
"""

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator
import structlog
from config.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

# SQLAlchemy setup with connection pooling
if "sqlite" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

async def init_db():
    """Initialize database and create tables"""
    try:
        logger.info("Initializing database connection")
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")

        # Enable pgvector extension (only for PostgreSQL)
        if "sqlite" not in settings.DATABASE_URL:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector extension enabled")

        # Create tables if they don't exist
        from services.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
            
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[Session, None]:
    """Get async database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def drop_tables():
    """Drop all database tables (for testing)"""
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")

# Updated 2025-09-05: Database connection and utilities with pgvector support