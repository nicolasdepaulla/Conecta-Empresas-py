from fastapi import APIRouter, Response, Depends, Request
from app.models.usuario import UsuarioCadastro, UsuarioLogin
from app.models.senha import SolicitarRedefinicaoSenha, RedefinirSenha
from app.services import usuario_service
from app.core.deps import get_current_user
from app.core.limiter import limiter

router = APIRouter(tags=["usuarios"])


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, dados: UsuarioCadastro):
    return await usuario_service.registrar(dados.username, dados.email, dados.password)


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, dados: UsuarioLogin, response: Response):
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
@limiter.limit("3/minute")
async def esqueci_senha(request: Request, dados: SolicitarRedefinicaoSenha):
    return await usuario_service.solicitar_redefinicao_senha(dados.email)


@router.post("/redefinir-senha")
@limiter.limit("5/minute")
async def redefinir_senha(request: Request, dados: RedefinirSenha):
    return await usuario_service.redefinir_senha(dados.token, dados.nova_senha)
