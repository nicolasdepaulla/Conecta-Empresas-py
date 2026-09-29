from datetime import datetime, timedelta, timezone
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


async def resumo_por_status():
    """Quantidade e valor total de pedidos, agrupados por status (pendente/pago/cancelado)."""
    pipeline = [
        {"$group": {"_id": "$status", "quantidade": {"$sum": 1}, "total": {"$sum": "$valor"}}}
    ]
    cursor = pedidos_collection.aggregate(pipeline)
    return [doc async for doc in cursor]


async def vendas_por_pacote():
    """Total vendido (só pedidos pagos) agrupado por pacote, do mais vendido pro menos."""
    pipeline = [
        {"$match": {"status": "pago"}},
        {"$group": {
            "_id": "$pacote_nome",
            "quantidade": {"$sum": 1},
            "total": {"$sum": "$valor"},
        }},
        {"$sort": {"total": -1}},
    ]
    cursor = pedidos_collection.aggregate(pipeline)
    return [doc async for doc in cursor]


async def vendas_por_dia(dias: int = 30):
    """Total vendido (só pedidos pagos) agrupado por dia, nos últimos `dias`."""
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    pipeline = [
        {"$match": {"status": "pago", "criado_em": {"$gte": desde}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$criado_em"}},
            "quantidade": {"$sum": 1},
            "total": {"$sum": "$valor"},
        }},
        {"$sort": {"_id": 1}},
    ]
    cursor = pedidos_collection.aggregate(pipeline)
    return [doc async for doc in cursor]
