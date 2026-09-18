from fastapi import APIRouter, Depends
from app.services import pacote_service
from app.core.deps import get_current_user

router = APIRouter(prefix="/pacotes", tags=["pacotes"])


@router.get("")
async def listar_pacotes(usuario: dict = Depends(get_current_user)):
    """Lista todos os pacotes disponíveis, cada um já com sua sessão de conteúdo."""
    pacotes = await pacote_service.listar_todos()
    for p in pacotes:
        p["_id"] = str(p["_id"])
        p["sessao"]["_id"] = str(p["sessao"]["_id"])
    return pacotes


@router.get("/{slug}")
async def obter_pacote(slug: str, usuario: dict = Depends(get_current_user)):
    """
    Substitui o antigo mapa fixo de arquivos HTML por setor (ex.: '/imobiliario',
    '/automotivo'): agora um único endpoint busca o pacote certo pelo slug.
    """
    pacote = await pacote_service.buscar_por_slug(slug)
    pacote["_id"] = str(pacote["_id"])
    pacote["sessao"]["_id"] = str(pacote["sessao"]["_id"])
    return pacote
