"""Testes para app/services/pacote_service.py."""
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.services import pacote_service


@pytest.fixture(autouse=True)
def mock_repository(monkeypatch):
    pacotes_falsos = [
        {"_id": "1", "slug": "imobiliario", "nome": "Pacote Imobiliário"},
        {"_id": "2", "slug": "automotivo", "nome": "Pacote Automotivo"},
    ]
    mocks = {
        "listar_pacotes": AsyncMock(return_value=pacotes_falsos),
        "buscar_por_slug": AsyncMock(return_value=pacotes_falsos[0]),
    }
    for nome, mock in mocks.items():
        monkeypatch.setattr(pacote_service.pacote_repository, nome, mock)
    return mocks


async def test_listar_todos_retorna_todos_os_pacotes(mock_repository):
    resultado = await pacote_service.listar_todos()

    assert len(resultado) == 2


async def test_buscar_por_slug_retorna_pacote_existente(mock_repository):
    resultado = await pacote_service.buscar_por_slug("imobiliario")

    assert resultado["nome"] == "Pacote Imobiliário"


async def test_buscar_por_slug_falha_com_404_quando_nao_encontrado(mock_repository):
    mock_repository["buscar_por_slug"].return_value = None

    with pytest.raises(HTTPException) as exc:
        await pacote_service.buscar_por_slug("nao-existe")

    assert exc.value.status_code == 404
