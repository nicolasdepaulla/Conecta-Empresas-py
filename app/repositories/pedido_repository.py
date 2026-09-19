from bson import ObjectId
from app.core.database import pedidos_collection


async def criar_pedido(pedido: dict) -> str:
    resultado = await pedidos_collection.insert_one(pedido)
    return str(resultado.inserted_id)


async def buscar_por_id(pedido_id: str):
    return await pedidos_collection.find_one({"_id": ObjectId(pedido_id)})


async def listar_por_usuario(username: str):
    cursor = pedidos_collection.find({"username": username}).sort("criado_em", -1)
    return [doc async for doc in cursor]


async def atualizar_status(pedido_id: str, status: str):
    await pedidos_collection.update_one(
        {"_id": ObjectId(pedido_id)}, {"$set": {"status": status}}
    )
