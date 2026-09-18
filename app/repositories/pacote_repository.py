from bson import ObjectId
from app.core.database import pacotes_collection


async def listar_pacotes():
    """Lista todos os pacotes já com a sessão resolvida (equivalente a um JOIN)."""
    pipeline = [
        {
            "$lookup": {
                "from": "sessoes",
                "let": {"sessaoId": {"$toObjectId": "$sessao_id"}},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$sessaoId"]}}}],
                "as": "sessao",
            }
        },
        {"$unwind": "$sessao"},
    ]
    return [doc async for doc in pacotes_collection.aggregate(pipeline)]


async def buscar_por_slug(slug: str):
    pipeline = [
        {"$match": {"slug": slug}},
        {
            "$lookup": {
                "from": "sessoes",
                "let": {"sessaoId": {"$toObjectId": "$sessao_id"}},
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$sessaoId"]}}}],
                "as": "sessao",
            }
        },
        {"$unwind": "$sessao"},
    ]
    resultados = [doc async for doc in pacotes_collection.aggregate(pipeline)]
    return resultados[0] if resultados else None


async def criar_pacote(pacote: dict) -> str:
    resultado = await pacotes_collection.insert_one(pacote)
    return str(resultado.inserted_id)
