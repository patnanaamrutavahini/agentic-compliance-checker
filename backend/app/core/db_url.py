def normalize_database_url(url: str) -> str:
    """Return an async SQLAlchemy URL for SQLite or PostgreSQL.

    Render/Heroku-style URLs (`postgres://...` or `postgresql://...`) are rewritten to
    the asyncpg driver so the same DATABASE_URL works everywhere.
    """
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    if url.startswith("sqlite://"):
        return "sqlite+aiosqlite://" + url[len("sqlite://"):]
    return url
