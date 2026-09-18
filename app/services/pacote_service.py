from fastapi import HTTPException
from app.repositories import pacote_repository


async def listar_todos():
    return await pacote_repository.listar_pacotes()


async def buscar_por_slug(slug: str):
    pacote = await pacote_repository.buscar_por_slug(slug)
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")
    return pacote
