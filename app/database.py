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
        port = int(os.getenv("DB_PORT", "5432"))
        query = {"sslmode": sslmode} if sslmode else {}
        # The Supabase shared pooler works over IPv4. Resolve A records
        # explicitly to avoid selecting unreachable IPv6 routes on hosts
        # without IPv6 access. Keep 'host' for TLS/SNI and auth routing.
        if host.endswith(".pooler.supabase.com"):
            import socket

            try:
                matches = socket.getaddrinfo(
                    host, port, family=socket.AF_INET, type=socket.SOCK_STREAM,
                )
                ipv4_addresses = list(dict.fromkeys(item[4][0] for item in matches))
            except socket.gaierror as exc:
                raise RuntimeError(
                    "Nao foi possivel resolver o IPv4 do Session Pooler Supabase na Discloud."
                ) from exc
            if not ipv4_addresses:
                raise RuntimeError("Session Pooler Supabase sem endereco IPv4 acessivel via DNS.")
            query["hostaddr"] = ipv4_addresses[0]
            print("AgendaFlow DB config: Supabase Session Pooler IPv4 selecionado.", flush=True)

        return URL.create(
            "postgresql+psycopg",
            username=os.getenv("DB_USER", "agenda").strip(),
            password=os.getenv("DB_PASSWORD", ""),
            host=host,
            port=port,
            database=os.getenv("DB_NAME", "agendaflow").strip(),
            query=query,
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
