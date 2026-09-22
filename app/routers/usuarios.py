from fastapi import APIRouter, Response, Depends
from app.models.usuario import UsuarioCadastro, UsuarioLogin
from app.models.senha import SolicitarRedefinicaoSenha, RedefinirSenha
from app.services import usuario_service
from app.core.deps import get_current_user

router = APIRouter(tags=["usuarios"])


@router.post("/register")
async def register(dados: UsuarioCadastro):
    return await usuario_service.registrar(dados.username, dados.email, dados.password)


@router.post("/login")
async def login(dados: UsuarioLogin, response: Response):
    token = await usuario_service.autenticar(dados.username, dados.password)
    response.set_cookie(
        key="authToken", value=token, httponly=True, secure=False, max_age=3600
    )
    return {"success": True, "message": "Login realizado com sucesso."}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("authToken")
    return {"success": True, "message": "Logout realizado."}


@router.get("/get-username")
async def get_username(usuario: dict = Depends(get_current_user)):
    return {"username": usuario["username"]}


@router.post("/esqueci-senha")
async def esqueci_senha(dados: SolicitarRedefinicaoSenha):
    return await usuario_service.solicitar_redefinicao_senha(dados.email)


@router.post("/redefinir-senha")
async def redefinir_senha(dados: RedefinirSenha):
    return await usuario_service.redefinir_senha(dados.token, dados.nova_senha)
