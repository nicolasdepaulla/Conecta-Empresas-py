"""
Rate limiting (limita quantas tentativas por IP em rotas sensíveis, como
login e redefinição de senha, pra dificultar ataques de força bruta).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
