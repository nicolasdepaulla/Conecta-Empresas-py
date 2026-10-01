"""
Repository de usuários -- migrado de MongoDB pra Postgres (via SQLAlchemy
async). Mantém os mesmos nomes de função e o retorno em dict dos services/
routers que já consomem esse módulo, pra eles não precisarem mudar nada.
"""
from datetime import datetime
from sqlalchemy import select, update
from app.core.postgres import AsyncSessionLocal
from app.models_sql.usuario import Usuario


def _to_dict(usuario: Usuario | None) -> dict | None:
    if usuario is None:
        return None
    return {
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "password": usuario.password,
        "is_admin": usuario.is_admin,
        "reset_token": usuario.reset_token,
        "reset_token_expira": usuario.reset_token_expira,
        "criado_em": usuario.criado_em,
    }


async def buscar_por_username(username: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(select(Usuario).where(Usuario.username == username))
        return _to_dict(resultado.scalar_one_or_none())


async def buscar_por_email(email: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(select(Usuario).where(Usuario.email == email))
        return _to_dict(resultado.scalar_one_or_none())


async def criar_usuario(username: str, email: str, hashed_password: str) -> dict:
    async with AsyncSessionLocal() as session:
        usuario = Usuario(username=username, email=email, password=hashed_password)
        session.add(usuario)
        # Deixa o IntegrityError (violação do UNIQUE de username/email)
        # propagar pro service -- é a segunda camada de proteção contra a
        # corrida entre dois cadastros simultâneos com o mesmo e-mail.
        await session.commit()
        await session.refresh(usuario)
        return _to_dict(usuario)


async def salvar_token_redefinicao(username: str, token: str, expira_em: datetime):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Usuario)
            .where(Usuario.username == username)
            .values(reset_token=token, reset_token_expira=expira_em)
        )
        await session.commit()


async def buscar_por_token_redefinicao(token: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(select(Usuario).where(Usuario.reset_token == token))
        return _to_dict(resultado.scalar_one_or_none())


async def atualizar_senha(username: str, nova_senha_hash: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Usuario)
            .where(Usuario.username == username)
            .values(password=nova_senha_hash, reset_token=None, reset_token_expira=None)
        )
        await session.commit()


async def marcar_como_admin(username: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Usuario).where(Usuario.username == username).values(is_admin=True)
        )
        await session.commit()
