from fastapi import APIRouter, Depends
from app.core.deps import get_current_user

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])

# Placeholder até a integração real do gateway (Mercado Pago / Pagar.me / Asaas).
# No original, os IDs 100/110/120/130 eram páginas HTML fixas; aqui viram
# apenas os valores de referência, e o checkout de verdade entra no service
# quando a integração for implementada.
TABELA_PRECOS = {"100": 100.00, "110": 110.00, "120": 120.00, "130": 130.00, "140": 1000.00}


@router.get("/{cobrar_id}")
async def obter_cobranca(cobrar_id: str, usuario: dict = Depends(get_current_user)):
    valor = TABELA_PRECOS.get(cobrar_id)
    return {"cobrar_id": cobrar_id, "valor": valor, "status": "aguardando_integracao"}
