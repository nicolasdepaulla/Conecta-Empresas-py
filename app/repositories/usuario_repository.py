from app.core.database import usuarios_collection


async def buscar_por_username(username: str):
    return await usuarios_collection.find_one({"username": username})


async def criar_usuario(username: str, email: str, hashed_password: str):
    return await usuarios_collection.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password,
    })
