from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

pacotes_collection = db["pacotes"]
sessoes_collection = db["sessoes"]
usuarios_collection = db["usuarios"]
pedidos_collection = db["pedidos"]
