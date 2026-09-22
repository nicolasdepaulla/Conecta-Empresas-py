"""Testes para app/services/usuario_service.py, sem tocar no MongoDB de verdade."""
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.services import usuario_service


@pytest.fixture(autouse=True)
def mock_repository(monkeypatch):
    """Substitui as funções do usuario_repository por versões falsas (AsyncMock)."""
    mocks = {
        "buscar_por_username": AsyncMock(return_value=None),
        "criar_usuario": AsyncMock(return_value=None),
    }
    for nome, mock in mocks.items():
        monkeypatch.setattr(usuario_service.usuario_repository, nome, mock)
    return mocks


async def test_registrar_cria_usuario_quando_username_disponivel(mock_repository):
    resultado = await usuario_service.registrar("nick", "nick@teste.com", "senha123")

    assert resultado["success"] is True
    mock_repository["criar_usuario"].assert_awaited_once()
    # A senha salva no banco nunca pode ser a senha em texto puro
    args = mock_repository["criar_usuario"].await_args.args
    assert args[2] != "senha123"


async def test_registrar_rejeita_username_ja_existente(mock_repository):
    mock_repository["buscar_por_username"].return_value = {"username": "nick"}

    with pytest.raises(HTTPException) as exc:
        await usuario_service.registrar("nick", "nick@teste.com", "senha123")

    assert exc.value.status_code == 409
    mock_repository["criar_usuario"].assert_not_awaited()


async def test_autenticar_aceita_senha_correta(mock_repository):
    from app.core.security import hash_password
    mock_repository["buscar_por_username"].return_value = {
        "username": "nick", "password": hash_password("senha123")
    }

    token = await usuario_service.autenticar("nick", "senha123")

    assert isinstance(token, str) and len(token) > 0


async def test_autenticar_rejeita_senha_errada(mock_repository):
    from app.core.security import hash_password
    mock_repository["buscar_por_username"].return_value = {
        "username": "nick", "password": hash_password("senha123")
    }

    with pytest.raises(HTTPException) as exc:
        await usuario_service.autenticar("nick", "senhaerrada")

    assert exc.value.status_code == 401


async def test_autenticar_rejeita_usuario_inexistente(mock_repository):
    mock_repository["buscar_por_username"].return_value = None

    with pytest.raises(HTTPException) as exc:
        await usuario_service.autenticar("naoexiste", "qualquersenha")

    assert exc.value.status_code == 401
