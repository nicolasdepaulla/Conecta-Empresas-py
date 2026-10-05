import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import usuarios, pacotes, pagamentos, admin
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.limiter import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.config import settings

# Em desenvolvimento os logs saem em DEBUG (mostra tudo, útil pra investigar
# bugs); em produção sobem pra INFO, pra não poluir/registrar informação
# demais. Controlado pela variável AMBIENTE.
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)

app = FastAPI(title="Conecta Empresas API")

app.add_middleware(SecurityHeadersMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(usuarios.router)
app.include_router(pacotes.router)
app.include_router(pagamentos.router)
app.include_router(admin.router)

# O índice único de email (antes criado no startup, via garantir_indices())
# agora é a constraint UNIQUE da coluna usuarios.email no Postgres -- não
# precisa de nenhum passo de inicialização pra isso.

# Serve o front-end (equivalente ao express.static('public') do projeto original)
app.mount("/", StaticFiles(directory="public", html=True), name="public")
