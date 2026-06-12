from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import get_settings

engine = None
async_session_maker = None

def init_db(settings=None):
    global engine, async_session_maker
    if not settings:
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
    return async_session_maker

async def get_db():
    maker = async_session_maker or init_db()
    async with maker() as session:
        yield session
