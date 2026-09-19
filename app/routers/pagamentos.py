from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.services import pedido_service

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])

TABELA_PRECOS = {"100": 100.00, "110": 110.00, "120": 120.00, "130": 130.00, "140": 1000.00}


@router.get("/{cobrar_id}")
async def obter_cobranca(cobrar_id: str, usuario: dict = Depends(get_current_user)):
    valor = TABELA_PRECOS.get(cobrar_id)
    return {"cobrar_id": cobrar_id, "valor": valor, "status": "aguardando_integracao"}


@router.post("/checkout/{slug_pacote}")
async def iniciar_checkout(slug_pacote: str, usuario: dict = Depends(get_current_user)):
    """Cria um pedido pendente para o pacote escolhido."""
    return await pedido_service.criar_pedido_para_checkout(usuario["username"], slug_pacote)


@router.post("/webhook")
async def webhook_pagamento(payload: dict):
    """
    Endpoint chamado pelo Mercado Pago quando o status de um pagamento muda.
    Para o Checkout Pro (Preferences), a notificação vem no formato:
    {"type": "payment", "data": {"id": "<payment_id>"}}
    """
    if payload.get("type") != "payment":
        return {"ignored": True, "reason": "evento não é de pagamento"}

    payment_id = (payload.get("data") or {}).get("id")
    if not payment_id:
        return {"ignored": True, "reason": "payload sem data.id"}

    return await pedido_service.confirmar_pagamento_por_id(payment_id)


@router.get("/pedidos/meus")
async def meus_pedidos(usuario: dict = Depends(get_current_user)):
    return await pedido_service.historico_do_usuario(usuario["username"])