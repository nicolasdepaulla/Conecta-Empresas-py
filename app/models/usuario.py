from pydantic import BaseModel, EmailStr, Field


class UsuarioCadastro(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=6)


class UsuarioLogin(BaseModel):
    username: str
    password: str


class UsuarioSaida(BaseModel):
    username: str
    email: EmailStr
