from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import usuarios, pacotes, pagamentos

app = FastAPI(title="Conecta Empresas API")

app.include_router(usuarios.router)
app.include_router(pacotes.router)
app.include_router(pagamentos.router)

# Serve o front-end (equivalente ao express.static('public') do projeto original)
app.mount("/", StaticFiles(directory="public", html=True), name="public")
