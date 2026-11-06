import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def database_url():
    """Prefer explicit DB_* fields over potentially inherited DATABASE_URL.

    The separate fields are safe for passwords containing URL delimiters such as @.
    DATABASE_URL remains supported when DB_HOST is not explicitly configured.
    """
    host = os.getenv("DB_HOST", "").strip()
    if host:
        # Never log the database password, full connection string or DB_USER.
        print("AgendaFlow DB config: using DB_* variables (ignoring DATABASE_URL).", flush=True)
        sslmode = os.getenv("DB_SSLMODE", "").strip()
        if not sslmode and host.endswith(".supabase.com"):
            sslmode = "require"
        return URL.create(
            "postgresql+psycopg",
            username=os.getenv("DB_USER", "agenda").strip(),
            password=os.getenv("DB_PASSWORD", ""),
            host=host,
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "agendaflow").strip(),
            query={"sslmode": sslmode} if sslmode else {},
        )

    override = os.getenv("DATABASE_URL", "").strip()
    if override:
        print("AgendaFlow DB config: using DATABASE_URL (DB_HOST not set).", flush=True)
        return override
    # Keep existing Docker Compose default when no database variables were set.
    print("AgendaFlow DB config: using local Docker defaults.", flush=True)
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_USER", "agenda"),
        password=os.getenv("DB_PASSWORD", ""),
        host="db",
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "agendaflow"),
    )


engine = create_engine(database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
