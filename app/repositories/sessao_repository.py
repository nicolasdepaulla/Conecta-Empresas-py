"""
Repository de sessões -- migrado de MongoDB pra Postgres (SQLAlchemy
async). Mantém os mesmos nomes de função e o retorno em dict (chave
"_id", igual ao Mongo) pros consumidores não precisarem mudar.
"""
from sqlalchemy import select
from app.core.postgres import AsyncSessionLocal
from app.models_sql.sessao import Sessao


def _to_dict(sessao: Sessao | None) -> dict | None:
    if sessao is None:
        return None
    return {"_id": sessao.id, "titulo": sessao.titulo, "itens": list(sessao.itens)}


async def buscar_por_id(sessao_id: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(select(Sessao).where(Sessao.id == int(sessao_id)))
        return _to_dict(resultado.scalar_one_or_none())


async def criar_sessao(titulo: str, itens: list[str]) -> str:
    async with AsyncSessionLocal() as session:
        sessao = Sessao(titulo=titulo, itens=itens)
        session.add(sessao)
        await session.commit()
        await session.refresh(sessao)
        return str(sessao.id)
