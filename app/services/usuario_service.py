from fastapi import HTTPException
import secrets
import logging
from datetime import datetime, timedelta, timezone
from pymongo.errors import DuplicateKeyError
from app.core.security import hash_password, verify_password, create_access_token
from app.core.email import enviar_email_redefinicao_senha
from app.core.config import settings
from app.repositories import usuario_repository

logger = logging.getLogger("conecta.usuarios")


async def registrar(username: str, email: str, password: str):
    existente = await usuario_repository.buscar_por_username(username)
    if existente:
        raise HTTPException(status_code=409, detail="Usuário já cadastrado.")

    existente_email = await usuario_repository.buscar_por_email(email)
    if existente_email:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")

    hashed = hash_password(password)
    try:
        await usuario_repository.criar_usuario(username, email, hashed)
    except DuplicateKeyError:
        # Segunda camada de proteção (índice único no Mongo), cobrindo a
        # corrida entre duas requisições de cadastro simultâneas com o
        # mesmo e-mail -- a checagem acima sozinha não é atômica.
        raise HTTPException(status_code=409, detail="E-mail já cadastrado.")

    return {"success": True, "message": "Usuário cadastrado com sucesso!"}


async def autenticar(username: str, password: str) -> str:
    """Retorna o token JWT em caso de sucesso, ou levanta 401."""
    usuario = await usuario_repository.buscar_por_username(username)
    if not usuario or not verify_password(password, usuario["password"]):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

    return create_access_token(usuario["username"])


async def solicitar_redefinicao_senha(email: str):
    """
    Por segurança, essa função sempre retorna sucesso, exista ou não o
    e-mail cadastrado -- assim não dá pra usar essa rota pra descobrir quais
    e-mails têm conta no sistema.
    """
    usuario = await usuario_repository.buscar_por_email(email)
    if usuario:
        token = secrets.token_urlsafe(32)
        expira_em = datetime.now(timezone.utc) + timedelta(minutes=30)
        await usuario_repository.salvar_token_redefinicao(usuario["username"], token, expira_em)

        link = f"{settings.public_base_url.rstrip('/')}/redefinir-senha.html?token={token}"
        enviar_email_redefinicao_senha(email, link)

    return {"success": True, "message": "Se o e-mail existir, um link de redefinição foi enviado."}


async def redefinir_senha(token: str, nova_senha: str):
    usuario = await usuario_repository.buscar_por_token_redefinicao(token)
    logger.debug("Redefinição de senha: usuário encontrado=%s", usuario is not None)
    if not usuario:
        raise HTTPException(status_code=400, detail="Link inválido ou expirado.")

    expira_em = usuario.get("reset_token_expira")
    agora = datetime.now(timezone.utc)
    if not expira_em or agora > expira_em.replace(tzinfo=timezone.utc):
        logger.info("Tentativa de redefinição com token expirado (usuário=%s)", usuario["username"])
        raise HTTPException(status_code=400, detail="Link inválido ou expirado.")

    nova_senha_hash = hash_password(nova_senha)
    await usuario_repository.atualizar_senha(usuario["username"], nova_senha_hash)
    logger.info("Senha redefinida com sucesso (usuário=%s)", usuario["username"])
    return {"success": True, "message": "Senha redefinida com sucesso."}
