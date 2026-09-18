from fastapi import HTTPException
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories import usuario_repository


async def registrar(username: str, email: str, password: str):
    existente = await usuario_repository.buscar_por_username(username)
    if existente:
        raise HTTPException(status_code=409, detail="Usuário já cadastrado.")

    hashed = hash_password(password)
    await usuario_repository.criar_usuario(username, email, hashed)
    return {"success": True, "message": "Usuário cadastrado com sucesso!"}


async def autenticar(username: str, password: str) -> str:
    """Retorna o token JWT em caso de sucesso, ou levanta 401."""
    usuario = await usuario_repository.buscar_por_username(username)
    if not usuario or not verify_password(password, usuario["password"]):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

    return create_access_token(usuario["username"])
