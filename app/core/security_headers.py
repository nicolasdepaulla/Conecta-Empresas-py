"""
Cabeçalhos de segurança HTTP que o FastAPI não define sozinho.

Não inclui Content-Security-Policy de propósito: as páginas em public/
usam <script> inline, então uma CSP restritiva quebraria o front-end hoje
-- fica pra quando o front-end passar por uma revisão (mover os scripts
pra arquivos .js separados primeiro).
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resposta = await call_next(request)

        # Impede o navegador de "adivinhar" o tipo de um arquivo servido
        # (evita, por exemplo, que um .txt enviado por um usuário seja
        # interpretado como HTML/JS executável).
        resposta.headers["X-Content-Type-Options"] = "nosniff"

        # Impede que a aplicação seja carregada dentro de um <iframe> em
        # outro site (proteção contra clickjacking).
        resposta.headers["X-Frame-Options"] = "DENY"

        # Evita vazar a URL completa (que pode conter token de redefinição
        # de senha, por exemplo) como "Referer" pra outros sites.
        resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS só faz sentido (e só é respeitado pelo navegador) quando a
        # conexão já é HTTPS -- em produção, atrás do Nginx com certificado.
        if settings.is_production:
            resposta.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"

        return resposta
