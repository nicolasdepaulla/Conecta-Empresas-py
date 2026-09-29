"""
Integração com o Checkout Pro do Mercado Pago via API de Preferences.
Docs: https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/landing
"""
import hashlib
import hmac
import logging
import httpx
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger("conecta.webhook")

PREFERENCES_URL = "https://api.mercadopago.com/checkout/preferences"


def validar_assinatura_webhook(x_signature: str | None, x_request_id: str | None, data_id: str) -> bool:
    """
    Valida a assinatura HMAC-SHA256 enviada pelo Mercado Pago no header
    x-signature, conforme a documentação oficial:
    https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/additional-content/notifications/webhooks

    Formato do header: "ts=<timestamp>,v1=<assinatura>"
    manifest = "id:{data_id};request-id:{x_request_id};ts:{ts};"
    assinatura esperada = HMAC-SHA256(manifest, PAYMENT_PROVIDER_WEBHOOK_SECRET)

    NOTA: esta função estava referenciada em app/routers/pagamentos.py mas
    não existia neste código-fonte -- implementada agora junto com os
    testes automatizados do webhook.
    """
    if not settings.payment_provider_webhook_secret:
        logger.warning("PAYMENT_PROVIDER_WEBHOOK_SECRET não configurado; rejeitando webhook.")
        return False

    if not x_signature:
        return False

    partes = dict(
        parte.strip().split("=", 1)
        for parte in x_signature.split(",")
        if "=" in parte
    )
    ts = partes.get("ts")
    v1 = partes.get("v1")
    if not ts or not v1:
        return False

    manifest = f"id:{data_id.lower()};"
    if x_request_id:
        manifest += f"request-id:{x_request_id};"
    manifest += f"ts:{ts};"

    assinatura_calculada = hmac.new(
        settings.payment_provider_webhook_secret.encode(),
        manifest.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(assinatura_calculada, v1)


async def criar_ordem_de_pagamento(
    pedido_id: str, valor: float, descricao: str, email_comprador: str | None = None
) -> dict:
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
    if email_comprador:
        payload["payer"] = {"email": email_comprador}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resposta = await client.post(PREFERENCES_URL, headers=headers, json=payload)

    if resposta.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao criar cobrança no Mercado Pago: {resposta.text}",
        )

    dados = resposta.json()
    # A documentação oficial do Mercado Pago recomenda usar init_point (não
    # sandbox_init_point) mesmo em testes com credenciais TEST-...; usar o
    # sandbox costuma gerar erro/travamento no checkout.
    checkout_url = dados.get("init_point") or dados.get("sandbox_init_point")
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
