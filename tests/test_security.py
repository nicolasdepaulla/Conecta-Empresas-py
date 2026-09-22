"""Testes para hash de senha e geração/validação de JWT (app/core/security.py)."""
from app.core import security


def test_hash_password_gera_hash_diferente_da_senha_original():
    senha = "minhasenha123"
    hash_gerado = security.hash_password(senha)

    assert hash_gerado != senha
    assert hash_gerado.startswith("$2b$")  # prefixo padrão do bcrypt


def test_verify_password_aceita_senha_correta():
    senha = "minhasenha123"
    hash_gerado = security.hash_password(senha)

    assert security.verify_password(senha, hash_gerado) is True


def test_verify_password_rejeita_senha_errada():
    hash_gerado = security.hash_password("minhasenha123")

    assert security.verify_password("senhaerrada", hash_gerado) is False


def test_create_and_decode_access_token_ida_e_volta():
    token = security.create_access_token("nick")
    payload = security.decode_access_token(token)

    assert payload is not None
    assert payload["username"] == "nick"


def test_decode_access_token_rejeita_token_invalido():
    payload = security.decode_access_token("token.invalido.aqui")

    assert payload is None
