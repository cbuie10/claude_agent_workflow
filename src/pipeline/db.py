"""Database connection utilities."""

from sqlalchemy import create_engine, text

from pipeline.config import DATABASE_URL


def get_engine(url: str = DATABASE_URL):
    """Create a SQLAlchemy engine for PostgreSQL."""
    return create_engine(url)


def check_connection(url: str = DATABASE_URL) -> bool:
    """Verify the database is reachable."""
    engine = get_engine(url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
