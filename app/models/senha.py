from pydantic import BaseModel, EmailStr, Field


class SolicitarRedefinicaoSenha(BaseModel):
    email: EmailStr


class RedefinirSenha(BaseModel):
    token: str
    # Mesma regra mínima do cadastro (UsuarioCadastro.password) -- antes
    # essa rota não validava nada, então dava pra redefinir pra uma senha
    # de 1 caractere mesmo exigindo 8+ no cadastro.
    nova_senha: str = Field(min_length=8)
