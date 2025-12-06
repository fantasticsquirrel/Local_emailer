from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()

database_url = settings.DATABASE_URL
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _run_sqlite_migrations()


def _run_sqlite_migrations() -> None:
    """Apply lightweight, in-code migrations for SQLite deployments."""

    if not database_url.startswith("sqlite"):
        return

    with engine.begin() as conn:
        has_source_column = any(
            row[1] == "source"
            for row in conn.execute(text("PRAGMA table_info('queued_emails')"))
        )

        if not has_source_column:
            conn.execute(
                text(
                    "ALTER TABLE queued_emails ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'"
                )
            )
