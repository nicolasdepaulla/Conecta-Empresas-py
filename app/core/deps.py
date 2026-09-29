from fastapi import Request, Depends, HTTPException
from app.core.security import decode_access_token
from app.repositories import usuario_repository


def get_current_user(request: Request) -> dict:
    """Equivalente ao authenticateToken do projeto original: lê o JWT do cookie."""
    token = request.cookies.get("authToken")
    if not token:
        raise HTTPException(status_code=401, detail="Acesso negado. Token não fornecido.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Token inválido.")

    return payload


async def get_current_admin_user(usuario: dict = Depends(get_current_user)) -> dict:
    """
    Exige que o usuário autenticado tenha is_admin=True.
    O JWT só carrega o username, então busca o usuário no banco pra checar a
    flag -- assim, revogar o acesso admin não depende do token expirar.
    """
    usuario_db = await usuario_repository.buscar_por_username(usuario["username"])
    if not usuario_db or not usuario_db.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")

    return usuario_db
