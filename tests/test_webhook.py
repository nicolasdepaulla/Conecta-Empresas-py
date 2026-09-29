"""
Testes para o webhook de pagamento (POST /pagamentos/webhook) e para a
validação de assinatura HMAC do Mercado Pago.

Cobre:
- assinatura válida/inválida (401 quando inválida)
- notificação duplicada/idempotência (não reprocessa pedido já pago)
- pedido inexistente e pedido já pago referenciados pelo webhook
"""
import hashlib
import hmac

import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services import mercadopago_service, pedido_service

# Sem `with`, o TestClient não dispara o evento de startup (que tentaria
# conectar num Mongo real) -- só processa as requisições feitas nele.
client = TestClient(app)


def _assinatura_valida(data_id: str, request_id: str, ts: str, secret: str) -> str:
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    v1 = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return f"ts={ts},v1={v1}"


# ---------------------------------------------------------------------------
# validar_assinatura_webhook (unitário)
# ---------------------------------------------------------------------------

def test_assinatura_valida_e_aceita(monkeypatch):
    monkeypatch.setattr(settings, "payment_provider_webhook_secret", "segredo123")
    x_signature = _assinatura_valida("123456789", "req-1", "1700000000", "segredo123")

    assert mercadopago_service.validar_assinatura_webhook(
        x_signature=x_signature, x_request_id="req-1", data_id="123456789"
    ) is True


def test_assinatura_com_v1_incorreto_e_rejeitada(monkeypatch):
    monkeypatch.setattr(settings, "payment_provider_webhook_secret", "segredo123")

    assert mercadopago_service.validar_assinatura_webhook(
        x_signature="ts=1700000000,v1=assinaturaforjada",
        x_request_id="req-1",
        data_id="123456789",
    ) is False


def test_assinatura_ausente_e_rejeitada(monkeypatch):
    monkeypatch.setattr(settings, "payment_provider_webhook_secret", "segredo123")

    assert mercadopago_service.validar_assinatura_webhook(
        x_signature=None, x_request_id="req-1", data_id="123456789"
    ) is False


def test_sem_webhook_secret_configurado_rejeita_tudo(monkeypatch):
    monkeypatch.setattr(settings, "payment_provider_webhook_secret", "")

    assert mercadopago_service.validar_assinatura_webhook(
        x_signature="ts=1700000000,v1=qualquercoisa", x_request_id="req-1", data_id="123"
    ) is False


# ---------------------------------------------------------------------------
# POST /pagamentos/webhook (integração via TestClient)
# ---------------------------------------------------------------------------

def test_webhook_com_assinatura_invalida_retorna_401(monkeypatch):
    monkeypatch.setattr(mercadopago_service, "validar_assinatura_webhook", lambda **kwargs: False)
    confirmar_mock = AsyncMock()
    monkeypatch.setattr(pedido_service, "confirmar_pagamento_por_id", confirmar_mock)

    resposta = client.post(
        "/pagamentos/webhook",
        json={"type": "payment", "data": {"id": "999"}},
        headers={"x-signature": "ts=1,v1=invalido", "x-request-id": "req-1"},
    )

    assert resposta.status_code == 401
    confirmar_mock.assert_not_awaited()


def test_webhook_com_assinatura_valida_processa_pagamento(monkeypatch):
    monkeypatch.setattr(mercadopago_service, "validar_assinatura_webhook", lambda **kwargs: True)
    confirmar_mock = AsyncMock(
        return_value={"success": True, "pedido_id": "pedido123", "status_mp": "approved"}
    )
    monkeypatch.setattr(pedido_service, "confirmar_pagamento_por_id", confirmar_mock)

    resposta = client.post(
        "/pagamentos/webhook",
        json={"type": "payment", "data": {"id": "999"}},
        headers={"x-signature": "ts=1,v1=valido", "x-request-id": "req-1"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["pedido_id"] == "pedido123"
    confirmar_mock.assert_awaited_once_with("999")


def test_webhook_ignora_evento_que_nao_e_pagamento(monkeypatch):
    confirmar_mock = AsyncMock()
    monkeypatch.setattr(pedido_service, "confirmar_pagamento_por_id", confirmar_mock)

    resposta = client.post(
        "/pagamentos/webhook", json={"type": "merchant_order", "data": {"id": "999"}}
    )

    assert resposta.status_code == 200
    assert resposta.json()["ignored"] is True
    confirmar_mock.assert_not_awaited()


def test_webhook_ignora_payload_sem_data_id(monkeypatch):
    confirmar_mock = AsyncMock()
    monkeypatch.setattr(pedido_service, "confirmar_pagamento_por_id", confirmar_mock)

    resposta = client.post("/pagamentos/webhook", json={"type": "payment", "data": {}})

    assert resposta.status_code == 200
    assert resposta.json()["ignored"] is True
    confirmar_mock.assert_not_awaited()


# ---------------------------------------------------------------------------
# Idempotência e pedido inexistente/já pago (nível de serviço)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pedido_dependencies(monkeypatch):
    mocks = {
        "buscar_pagamento_por_id": AsyncMock(
            return_value={"external_reference": "pedido123", "status": "approved"}
        ),
        "buscar_por_id": AsyncMock(return_value={"_id": "pedido123", "status": "pendente"}),
        "atualizar_status": AsyncMock(return_value=None),
    }
    monkeypatch.setattr(mercadopago_service, "buscar_pagamento_por_id", mocks["buscar_pagamento_por_id"])
    monkeypatch.setattr(pedido_service.pedido_repository, "buscar_por_id", mocks["buscar_por_id"])
    monkeypatch.setattr(pedido_service.pedido_repository, "atualizar_status", mocks["atualizar_status"])
    return mocks


async def test_webhook_pedido_inexistente_retorna_404(mock_pedido_dependencies):
    mock_pedido_dependencies["buscar_por_id"].return_value = None

    with pytest.raises(HTTPException) as exc:
        await pedido_service.confirmar_pagamento_por_id("mp_payment_1")

    assert exc.value.status_code == 404


async def test_webhook_pedido_ja_pago_nao_reprocessa(mock_pedido_dependencies):
    mock_pedido_dependencies["buscar_por_id"].return_value = {"_id": "pedido123", "status": "pago"}

    resultado = await pedido_service.confirmar_pagamento_por_id("mp_payment_1")

    assert resultado["ja_processado"] is True
    mock_pedido_dependencies["atualizar_status"].assert_not_awaited()


async def test_webhook_notificacao_duplicada_e_idempotente(mock_pedido_dependencies):
    """Duas chamadas seguidas (retry do Mercado Pago) só atualizam o status uma vez."""
    await pedido_service.confirmar_pagamento_por_id("mp_payment_1")
    mock_pedido_dependencies["buscar_por_id"].return_value = {"_id": "pedido123", "status": "pago"}

    await pedido_service.confirmar_pagamento_por_id("mp_payment_1")

    mock_pedido_dependencies["atualizar_status"].assert_awaited_once_with("pedido123", "pago")
