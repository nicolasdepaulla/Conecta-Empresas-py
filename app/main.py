import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import usuarios, pacotes, pagamentos
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.limiter import limiter

# Garante que os logs de INFO (ex.: notificações do webhook do Mercado Pago)
# apareçam no terminal enquanto o servidor roda com uvicorn.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

app = FastAPI(title="Conecta Empresas API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(usuarios.router)
app.include_router(pacotes.router)
app.include_router(pagamentos.router)

# Serve o front-end (equivalente ao express.static('public') do projeto original)
app.mount("/", StaticFiles(directory="public", html=True), name="public")
