"""
Conexão assíncrona com o Postgres via SQLAlchemy.

Convive com o Mongo (app/core/database.py) enquanto a migração avança
repository por repository -- ver a issue "Migrar persistência de MongoDB
para PostgreSQL". Os models SQL (tabelas) entram na próxima etapa; por
enquanto só a infra de conexão e a Base usada pelas migrations do Alembic.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe base declarativa -- os models SQL (usuarios, pacotes, etc.) vão herdar dela."""
    pass


async def get_session() -> AsyncSession:
    """Dependência do FastAPI pra injetar uma sessão de banco nas rotas/services."""
    async with AsyncSessionLocal() as session:
        yield session
