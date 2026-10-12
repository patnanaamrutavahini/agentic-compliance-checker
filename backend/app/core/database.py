import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.db_url import normalize_database_url
from app.models.db_models import Base

logger = logging.getLogger(__name__)


DATABASE_URL = normalize_database_url(settings.DATABASE_URL)
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def database_dialect() -> str:
    return "postgresql" if IS_POSTGRES else DATABASE_URL.split(":", 1)[0].split("+", 1)[0]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready (%s).", database_dialect())


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
