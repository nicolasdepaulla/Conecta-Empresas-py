"""Testes para app/services/usuario_service.py, sem tocar no banco de verdade."""
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.services import usuario_service


@pytest.fixture(autouse=True)
def mock_repository(monkeypatch):
    """Substitui as funções do usuario_repository por versões falsas (AsyncMock)."""
    mocks = {
        "buscar_por_username": AsyncMock(return_value=None),
        "criar_usuario": AsyncMock(return_value=None),
        "buscar_por_email": AsyncMock(return_value=None),
        "salvar_token_redefinicao": AsyncMock(return_value=None),
        "buscar_por_token_redefinicao": AsyncMock(return_value=None),
        "atualizar_senha": AsyncMock(return_value=None),
    }
    for nome, mock in mocks.items():
        monkeypatch.setattr(usuario_service.usuario_repository, nome, mock)
    monkeypatch.setattr(usuario_service, "enviar_email_redefinicao_senha", lambda *a, **k: None)
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


async def test_registrar_rejeita_corrida_de_cadastro_com_mesmo_email(mock_repository):
    """
    Duas requisições de cadastro com o mesmo e-mail em paralelo passam pela
    checagem (nenhuma vê a outra ainda) e só a UNIQUE constraint do Postgres
    barra a segunda, na hora do INSERT -- o repository deixa o
    IntegrityError propagar, e o service precisa convertê-lo em 409.
    """
    mock_repository["criar_usuario"].side_effect = IntegrityError("INSERT", {}, Exception("duplicate key"))

    with pytest.raises(HTTPException) as exc:
        await usuario_service.registrar("nick", "nick@teste.com", "senha123")

    assert exc.value.status_code == 409


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


async def test_solicitar_redefinicao_gera_token_quando_email_existe(mock_repository):
    mock_repository["buscar_por_email"].return_value = {"username": "nick", "email": "nick@teste.com"}

    resultado = await usuario_service.solicitar_redefinicao_senha("nick@teste.com")

    assert resultado["success"] is True
    mock_repository["salvar_token_redefinicao"].assert_awaited_once()


async def test_solicitar_redefinicao_nao_falha_com_email_inexistente(mock_repository):
    mock_repository["buscar_por_email"].return_value = None

    resultado = await usuario_service.solicitar_redefinicao_senha("naoexiste@teste.com")

    # Sempre retorna sucesso, exista o e-mail ou não (evita vazar quais e-mails têm conta)
    assert resultado["success"] is True
    mock_repository["salvar_token_redefinicao"].assert_not_awaited()


async def test_redefinir_senha_com_token_valido(mock_repository):
    from datetime import datetime, timedelta, timezone
    mock_repository["buscar_por_token_redefinicao"].return_value = {
        "username": "nick",
        "reset_token_expira": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    resultado = await usuario_service.redefinir_senha("token-valido", "novasenha123")

    assert resultado["success"] is True
    mock_repository["atualizar_senha"].assert_awaited_once()


async def test_redefinir_senha_com_token_inexistente(mock_repository):
    mock_repository["buscar_por_token_redefinicao"].return_value = None

    with pytest.raises(HTTPException) as exc:
        await usuario_service.redefinir_senha("token-invalido", "novasenha123")

    assert exc.value.status_code == 400


async def test_redefinir_senha_com_token_expirado(mock_repository):
    from datetime import datetime, timedelta, timezone
    mock_repository["buscar_por_token_redefinicao"].return_value = {
        "username": "nick",
        "reset_token_expira": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    with pytest.raises(HTTPException) as exc:
        await usuario_service.redefinir_senha("token-expirado", "novasenha123")

    assert exc.value.status_code == 400
