"""Async SQLAlchemy boilerplate shared by services that persist state.

Each service owns its own Postgres schema (schema-per-service, one shared
database) so tables never collide and each service's models.py stays
self-contained.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def ensure_schema_and_tables(engine: AsyncEngine, schema: str, base: type[DeclarativeBase]) -> None:
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        await conn.run_sync(base.metadata.create_all)
