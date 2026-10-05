import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from app.core.deps import get_current_user
from app.services import pedido_service, mercadopago_service

logger = logging.getLogger("conecta.webhook")

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])


@router.post("/checkout/{slug_pacote}")
async def iniciar_checkout(slug_pacote: str, usuario: dict = Depends(get_current_user)):
    """Cria um pedido pendente para o pacote escolhido."""
    return await pedido_service.criar_pedido_para_checkout(usuario["username"], slug_pacote)


@router.post("/webhook")
async def webhook_pagamento(payload: dict, request: Request):
    """
    Endpoint chamado pelo Mercado Pago quando o status de um pagamento muda.
    Para o Checkout Pro (Preferences), a notificação vem no formato:
    {"type": "payment", "data": {"id": "<payment_id>"}}
    """
    # Loga só os campos que a aplicação de fato usa, não o payload inteiro
    # -- o Checkout Pro não manda dado de cartão aqui, mas não custa evitar
    # logar um payload bruto de terceiro inteiro caso o formato mude um dia.
    logger.info("Webhook recebido: type=%s data.id=%s", payload.get("type"), (payload.get("data") or {}).get("id"))

    if payload.get("type") != "payment":
        return {"ignored": True, "reason": "evento não é de pagamento"}

    payment_id = (payload.get("data") or {}).get("id")
    if not payment_id:
        return {"ignored": True, "reason": "payload sem data.id"}

    assinatura_valida = mercadopago_service.validar_assinatura_webhook(
        x_signature=request.headers.get("x-signature"),
        x_request_id=request.headers.get("x-request-id"),
        data_id=str(payment_id),
    )
    if not assinatura_valida:
        logger.warning("Webhook com assinatura inválida recebido (payment_id=%s)", payment_id)
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida.")

    resultado = await pedido_service.confirmar_pagamento_por_id(payment_id)
    logger.info("Pedido atualizado via webhook: %s", resultado)
    return resultado


@router.get("/pedidos/meus")
async def meus_pedidos(usuario: dict = Depends(get_current_user)):
    return await pedido_service.historico_do_usuario(usuario["username"])