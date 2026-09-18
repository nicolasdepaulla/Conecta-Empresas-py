from bson import ObjectId
from app.core.database import sessoes_collection


async def buscar_por_id(sessao_id: str):
    return await sessoes_collection.find_one({"_id": ObjectId(sessao_id)})


async def criar_sessao(titulo: str, itens: list[str]) -> str:
    resultado = await sessoes_collection.insert_one({"titulo": titulo, "itens": itens})
    return str(resultado.inserted_id)
