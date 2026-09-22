"""
Testes para app/services/pedido_service.py.

O ponto principal aqui é validar a lógica de checkout e de confirmação do
webhook SEM depender do checkout real do Mercado Pago (que trava no sandbox
por causa de bloqueio de cookies de terceiros no navegador) -- simulamos as
respostas da API deles.
"""
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.services import pedido_service


@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    pacote_falso = {
        "_id": "64f1a2b3c4d5e6f7a8b9c0d1",
        "slug": "imobiliario",
        "nome": "Pacote Premium Imobiliário",
        "preco": 100.0,
    }
    usuario_falso = {"username": "nick", "email": "nick@teste.com"}

    mocks = {
        "pacote_repository.buscar_por_slug": AsyncMock(return_value=pacote_falso),
        "usuario_repository.buscar_por_username": AsyncMock(return_value=usuario_falso),
        "pedido_repository.criar_pedido": AsyncMock(return_value="pedido123"),
        "pedido_repository.buscar_por_id": AsyncMock(return_value={"_id": "pedido123"}),
        "pedido_repository.atualizar_status": AsyncMock(return_value=None),
        "mercadopago_service.criar_ordem_de_pagamento": AsyncMock(
            return_value={"preference_id": "pref123", "checkout_url": "https://mp.test/checkout/pref123"}
        ),
        "mercadopago_service.buscar_pagamento_por_id": AsyncMock(),
    }
    for caminho, mock in mocks.items():
        modulo_attr, nome_func = caminho.split(".")
        monkeypatch.setattr(getattr(pedido_service, modulo_attr), nome_func, mock)
    return mocks


async def test_checkout_cria_pedido_e_retorna_checkout_url(mock_dependencies):
    resultado = await pedido_service.criar_pedido_para_checkout("nick", "imobiliario")

    assert resultado["pedido_id"] == "pedido123"
    assert resultado["valor"] == 100.0
    assert resultado["status"] == "pendente"
    assert resultado["checkout_url"] == "https://mp.test/checkout/pref123"


async def test_checkout_envia_email_do_comprador_para_o_mercado_pago(mock_dependencies):
    await pedido_service.criar_pedido_para_checkout("nick", "imobiliario")

    chamada = mock_dependencies["mercadopago_service.criar_ordem_de_pagamento"]
    chamada.assert_awaited_once()
    assert chamada.await_args.kwargs["email_comprador"] == "nick@teste.com"


async def test_checkout_falha_com_pacote_inexistente(mock_dependencies):
    mock_dependencies["pacote_repository.buscar_por_slug"].return_value = None

    with pytest.raises(HTTPException) as exc:
        await pedido_service.criar_pedido_para_checkout("nick", "pacote-que-nao-existe")

    assert exc.value.status_code == 404


async def test_webhook_confirma_pagamento_aprovado(mock_dependencies):
    mock_dependencies["mercadopago_service.buscar_pagamento_por_id"].return_value = {
        "external_reference": "pedido123", "status": "approved",
    }

    resultado = await pedido_service.confirmar_pagamento_por_id("mp_payment_1")

    assert resultado["status_mp"] == "approved"
    mock_dependencies["pedido_repository.atualizar_status"].assert_awaited_once_with(
        "pedido123", "pago"
    )


async def test_webhook_marca_pedido_como_cancelado_se_pagamento_rejeitado(mock_dependencies):
    mock_dependencies["mercadopago_service.buscar_pagamento_por_id"].return_value = {
        "external_reference": "pedido123", "status": "rejected",
    }

    await pedido_service.confirmar_pagamento_por_id("mp_payment_2")

    mock_dependencies["pedido_repository.atualizar_status"].assert_awaited_once_with(
        "pedido123", "cancelado"
    )


async def test_webhook_nao_atualiza_status_se_pagamento_ainda_pendente(mock_dependencies):
    mock_dependencies["mercadopago_service.buscar_pagamento_por_id"].return_value = {
        "external_reference": "pedido123", "status": "pending",
    }

    resultado = await pedido_service.confirmar_pagamento_por_id("mp_payment_3")

    assert resultado["status_mp"] == "pending"
    mock_dependencies["pedido_repository.atualizar_status"].assert_not_awaited()


async def test_webhook_falha_se_pagamento_sem_external_reference(mock_dependencies):
    mock_dependencies["mercadopago_service.buscar_pagamento_por_id"].return_value = {
        "status": "approved"
    }

    with pytest.raises(HTTPException) as exc:
        await pedido_service.confirmar_pagamento_por_id("mp_payment_4")

    assert exc.value.status_code == 400
