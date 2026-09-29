from fastapi import APIRouter, Depends
from app.core.deps import get_current_admin_user
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard(usuario: dict = Depends(get_current_admin_user)):
    """Retorna os números consolidados de vendas para a diretoria/admin."""
    return await admin_service.obter_dashboard()
