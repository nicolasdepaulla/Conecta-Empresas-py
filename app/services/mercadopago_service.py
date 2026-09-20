"""
Integração com o Checkout Pro do Mercado Pago via API de Preferences.
Docs: https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/landing
"""
import hmac
import hashlib
import httpx
from fastapi import HTTPException
from app.core.config import settings

PREFERENCES_URL = "https://api.mercadopago.com/checkout/preferences"


async def criar_ordem_de_pagamento(pedido_id: str, valor: float, descricao: str) -> dict:
    """
    Cria uma preferência de pagamento e devolve a URL de checkout (hospedada
    pelo Mercado Pago) pra redirecionar o comprador. external_reference liga
    a preferência ao nosso pedido no Mongo, pro webhook localizar depois.
    """
    if not settings.payment_provider_api_key:
        raise HTTPException(
            status_code=503,
            detail="Integração de pagamento não configurada (PAYMENT_PROVIDER_API_KEY ausente).",
        )

    headers = {
        "Authorization": f"Bearer {settings.payment_provider_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "items": [
            {
                "title": descricao,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": valor,
            }
        ],
        "external_reference": pedido_id,
    }
    if settings.public_base_url:
        payload["notification_url"] = f"{settings.public_base_url.rstrip('/')}/pagamentos/webhook"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resposta = await client.post(PREFERENCES_URL, headers=headers, json=payload)

    if resposta.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao criar cobrança no Mercado Pago: {resposta.text}",
        )

    dados = resposta.json()
    # Em modo de teste (Access Token TEST-...), use sandbox_init_point;
    # em produção, o init_point normal.
    checkout_url = dados.get("sandbox_init_point") or dados.get("init_point")
    return {"preference_id": dados.get("id"), "checkout_url": checkout_url, "raw": dados}


async def buscar_pagamentos_da_preferencia(external_reference: str) -> list:
    """Busca pagamentos associados a um external_reference (nosso pedido_id)."""
    headers = {"Authorization": f"Bearer {settings.payment_provider_api_key}"}
    params = {"external_reference": external_reference}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resposta = await client.get(
            "https://api.mercadopago.com/v1/payments/search", headers=headers, params=params
        )

    if resposta.status_code != 200:
        raise HTTPException(status_code=502, detail="Não foi possível consultar o pagamento no Mercado Pago.")

    return resposta.json().get("results", [])


async def buscar_pagamento_por_id(payment_id: str) -> dict:
    headers = {"Authorization": f"Bearer {settings.payment_provider_api_key}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resposta = await client.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers
        )

    if resposta.status_code != 200:
        raise HTTPException(status_code=502, detail="Não foi possível consultar o pagamento no Mercado Pago.")

    return resposta.json()


def validar_assinatura_webhook(x_signature: str | None, x_request_id: str | None, data_id: str | None) -> bool:
    """
    Valida a assinatura que o Mercado Pago envia no header 'x-signature' das
    notificações de webhook, evitando que qualquer um chame nosso endpoint
    fingindo ser o Mercado Pago.

    Formato do header: "ts=1704908010,v1=<hash_hmac_sha256>"
    Manifest assinado: "id:{data.id};request-id:{x-request-id};ts:{ts};"
    Docs: https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/additional-content/notifications/webhooks
    """
    if not settings.payment_provider_webhook_secret:
        # Sem segredo configurado ainda (ex.: primeiros testes em sandbox) -> não bloqueia.
        return True

    if not x_signature or not data_id:
        return False

    partes = dict(item.split("=", 1) for item in x_signature.split(",") if "=" in item)
    ts = partes.get("ts")
    v1_recebido = partes.get("v1")
    if not ts or not v1_recebido:
        return False

    manifest = f"id:{data_id.lower()};"
    if x_request_id:
        manifest += f"request-id:{x_request_id};"
    manifest += f"ts:{ts};"

    v1_calculado = hmac.new(
        settings.payment_provider_webhook_secret.encode(),
        manifest.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(v1_calculado, v1_recebido)