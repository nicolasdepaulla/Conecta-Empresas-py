from app.core.database import usuarios_collection


async def buscar_por_username(username: str):
    return await usuarios_collection.find_one({"username": username})


async def criar_usuario(username: str, email: str, hashed_password: str):
    return await usuarios_collection.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password,
    })


async def buscar_por_email(email: str):
    return await usuarios_collection.find_one({"email": email})


async def salvar_token_redefinicao(username: str, token: str, expira_em):
    await usuarios_collection.update_one(
        {"username": username},
        {"$set": {"reset_token": token, "reset_token_expira": expira_em}},
    )


async def buscar_por_token_redefinicao(token: str):
    return await usuarios_collection.find_one({"reset_token": token})


async def atualizar_senha(username: str, nova_senha_hash: str):
    await usuarios_collection.update_one(
        {"username": username},
        {"$set": {"password": nova_senha_hash}, "$unset": {"reset_token": "", "reset_token_expira": ""}},
    )


async def marcar_como_admin(username: str):
    await usuarios_collection.update_one(
        {"username": username},
        {"$set": {"is_admin": True}},
    )
