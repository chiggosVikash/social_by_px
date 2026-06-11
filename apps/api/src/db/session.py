from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with async_session_maker() as session:
        yield session
