from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

pacotes_collection = db["pacotes"]
sessoes_collection = db["sessoes"]
usuarios_collection = db["usuarios"]
pedidos_collection = db["pedidos"]


async def garantir_indices():
    """
    Cria os índices necessários no banco. Roda no startup da API.

    Atenção: se já existirem documentos com e-mail duplicado na
    collection `usuarios`, a criação do índice único abaixo vai falhar
    -- nesse caso, é preciso limpar/corrigir os duplicados manualmente
    antes de subir essa mudança.
    """
    await usuarios_collection.create_index("email", unique=True)
