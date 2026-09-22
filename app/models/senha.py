from pydantic import BaseModel, EmailStr


class SolicitarRedefinicaoSenha(BaseModel):
    email: EmailStr


class RedefinirSenha(BaseModel):
    token: str
    nova_senha: str
