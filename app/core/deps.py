from fastapi import Request, HTTPException
from app.core.security import decode_access_token


def get_current_user(request: Request) -> dict:
    """Equivalente ao authenticateToken do projeto original: lê o JWT do cookie."""
    token = request.cookies.get("authToken")
    if not token:
        raise HTTPException(status_code=401, detail="Acesso negado. Token não fornecido.")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Token inválido.")

    return payload
