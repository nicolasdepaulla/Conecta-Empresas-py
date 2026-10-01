"""
Models SQL (Postgres) -- importados aqui só pra garantir que fiquem
registrados em Base.metadata antes do Alembic rodar o autogenerate.
"""
from app.models_sql.usuario import Usuario
from app.models_sql.sessao import Sessao
from app.models_sql.pacote import Pacote
from app.models_sql.pedido import Pedido

__all__ = ["Usuario", "Sessao", "Pacote", "Pedido"]
