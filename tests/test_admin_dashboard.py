"""
Testes para o dashboard administrativo de vendas: cálculo dos números
agregados (admin_service), a checagem de admin (get_current_admin_user)
e o endpoint GET /admin/dashboard.
"""
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core import deps
from app.repositories import pedido_repository, usuario_repository
from app.services import admin_service

client = TestClient(app)


# ---------------------------------------------------------------------------
# admin_service.obter_dashboard
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_agregacoes(monkeypatch):
    monkeypatch.setattr(
        pedido_repository, "resumo_por_status",
        AsyncMock(return_value=[
            {"_id": "pago", "quantidade": 3, "total": 300.0},
            {"_id": "pendente", "quantidade": 1, "total": 100.0},
        ]),
    )
    monkeypatch.setattr(
        pedido_repository, "vendas_por_pacote",
        AsyncMock(return_value=[{"_id": "Pacote A", "quantidade": 2, "total": 200.0}]),
    )
    monkeypatch.setattr(
        pedido_repository, "vendas_por_dia",
        AsyncMock(return_value=[{"_id": "2026-09-28", "quantidade": 3, "total": 300.0}]),
    )


async def test_obter_dashboard_calcula_total_e_ticket_medio(mock_agregacoes):
    resultado = await admin_service.obter_dashboard()

    assert resultado["total_vendido"] == 300.0
    assert resultado["pedidos_pagos"] == 3
    assert resultado["ticket_medio"] == 100.0
    assert resultado["vendas_por_pacote"][0]["pacote"] == "Pacote A"
    assert resultado["vendas_por_dia"][0]["data"] == "2026-09-28"


async def test_obter_dashboard_sem_pedidos_pagos_ticket_medio_zero(monkeypatch):
    monkeypatch.setattr(pedido_repository, "resumo_por_status", AsyncMock(return_value=[]))
    monkeypatch.setattr(pedido_repository, "vendas_por_pacote", AsyncMock(return_value=[]))
    monkeypatch.setattr(pedido_repository, "vendas_por_dia", AsyncMock(return_value=[]))

    resultado = await admin_service.obter_dashboard()

    assert resultado["total_vendido"] == 0
    assert resultado["ticket_medio"] == 0.0


# ---------------------------------------------------------------------------
# get_current_admin_user
# ---------------------------------------------------------------------------

async def test_get_current_admin_user_permite_admin(monkeypatch):
    monkeypatch.setattr(
        usuario_repository, "buscar_por_username",
        AsyncMock(return_value={"username": "chefe", "is_admin": True}),
    )

    resultado = await deps.get_current_admin_user({"username": "chefe"})

    assert resultado["is_admin"] is True


async def test_get_current_admin_user_rejeita_usuario_comum(monkeypatch):
    monkeypatch.setattr(
        usuario_repository, "buscar_por_username",
        AsyncMock(return_value={"username": "cliente", "is_admin": False}),
    )

    with pytest.raises(HTTPException) as exc:
        await deps.get_current_admin_user({"username": "cliente"})

    assert exc.value.status_code == 403


async def test_get_current_admin_user_rejeita_usuario_inexistente(monkeypatch):
    monkeypatch.setattr(usuario_repository, "buscar_por_username", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc:
        await deps.get_current_admin_user({"username": "fantasma"})

    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# GET /admin/dashboard (integração)
# ---------------------------------------------------------------------------

def test_endpoint_dashboard_retorna_dados_quando_admin(monkeypatch):
    app.dependency_overrides[deps.get_current_admin_user] = lambda: {"username": "chefe", "is_admin": True}
    monkeypatch.setattr(
        admin_service, "obter_dashboard",
        AsyncMock(return_value={"total_vendido": 300.0, "ticket_medio": 100.0, "pedidos_pagos": 3}),
    )

    try:
        resposta = client.get("/admin/dashboard")
    finally:
        app.dependency_overrides.pop(deps.get_current_admin_user, None)

    assert resposta.status_code == 200
    assert resposta.json()["pedidos_pagos"] == 3


def test_endpoint_dashboard_retorna_403_para_usuario_comum(monkeypatch):
    monkeypatch.setattr(deps, "decode_access_token", lambda token: {"username": "cliente"})
    monkeypatch.setattr(
        usuario_repository, "buscar_por_username",
        AsyncMock(return_value={"username": "cliente", "is_admin": False}),
    )

    resposta = client.get("/admin/dashboard", headers={"Cookie": "authToken=qualquer"})

    assert resposta.status_code == 403
