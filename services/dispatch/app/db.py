from resq_shared.db import make_engine, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings

engine = make_engine(settings.database_url)
SessionLocal = make_session_factory(engine)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
