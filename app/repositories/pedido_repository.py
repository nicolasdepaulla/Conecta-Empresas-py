"""
Repository de pedidos -- migrado de MongoDB pra Postgres (SQLAlchemy
async). É o repository mais usado (checkout, webhook de pagamento,
histórico do usuário e dashboard administrativo), então aqui o cuidado
maior foi não mudar nada do que os services já esperam.

Duas diferenças internas em relação à versão Mongo, escondidas dos
consumidores:
- O pedido guarda `usuario_id` (FOREIGN KEY de verdade), não `username`.
  Como pedido_service.py sempre trabalha com `username`, esse repository
  resolve o username pro id internamente -- pedido_service.py não mudou.
- As agregações do dashboard (resumo_por_status, vendas_por_pacote,
  vendas_por_dia), que eram pipelines do Mongo, agora são GROUP BY/SUM
  de verdade no Postgres. O formato de retorno (lista de dicts com
  "_id"/"quantidade"/"total") é o mesmo que admin_service.py já espera,
  então ele também não precisou mudar.
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import joinedload
from app.core.postgres import AsyncSessionLocal
from app.models.pedido import StatusPedido
from app.models_sql.pedido import Pedido
from app.models_sql.usuario import Usuario


def _to_dict(pedido: Pedido, username: str) -> dict:
    return {
        "_id": pedido.id,
        "username": username,
        "pacote_id": str(pedido.pacote_id),
        "pacote_nome": pedido.pacote_nome,
        "valor": float(pedido.valor),
        "status": pedido.status.value,
        "criado_em": pedido.criado_em,
    }


async def criar_pedido(pedido: dict) -> str:
    async with AsyncSessionLocal() as session:
        usuario_id = (
            await session.execute(select(Usuario.id).where(Usuario.username == pedido["username"]))
        ).scalar_one()

        novo = Pedido(
            usuario_id=usuario_id,
            pacote_id=int(pedido["pacote_id"]),
            pacote_nome=pedido["pacote_nome"],
            valor=pedido["valor"],
            status=StatusPedido(pedido.get("status", StatusPedido.pendente.value)),
        )
        session.add(novo)
        await session.commit()
        await session.refresh(novo)
        return str(novo.id)


async def buscar_por_id(pedido_id: str):
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(Pedido).options(joinedload(Pedido.usuario)).where(Pedido.id == int(pedido_id))
        )
        pedido = resultado.scalar_one_or_none()
        if pedido is None:
            return None
        return _to_dict(pedido, pedido.usuario.username)


async def listar_por_usuario(username: str):
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(Pedido)
            .join(Usuario, Pedido.usuario_id == Usuario.id)
            .where(Usuario.username == username)
            .order_by(Pedido.criado_em.desc())
        )
        return [_to_dict(p, username) for p in resultado.scalars().all()]


async def atualizar_status(pedido_id: str, status: str):
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(select(Pedido).where(Pedido.id == int(pedido_id)))
        pedido = resultado.scalar_one_or_none()
        if pedido is None:
            return
        pedido.status = StatusPedido(status)
        await session.commit()


async def resumo_por_status():
    """Quantidade e valor total de pedidos, agrupados por status (pendente/pago/cancelado)."""
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(Pedido.status, func.count(Pedido.id), func.sum(Pedido.valor)).group_by(Pedido.status)
        )
        return [
            {"_id": status.value, "quantidade": quantidade, "total": float(total or 0)}
            for status, quantidade, total in resultado.all()
        ]


async def vendas_por_pacote():
    """Total vendido (só pedidos pagos) agrupado por pacote, do mais vendido pro menos."""
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(Pedido.pacote_nome, func.count(Pedido.id), func.sum(Pedido.valor))
            .where(Pedido.status == StatusPedido.pago)
            .group_by(Pedido.pacote_nome)
            .order_by(func.sum(Pedido.valor).desc())
        )
        return [
            {"_id": nome, "quantidade": quantidade, "total": float(total or 0)}
            for nome, quantidade, total in resultado.all()
        ]


async def vendas_por_dia(dias: int = 30):
    """Total vendido (só pedidos pagos) agrupado por dia, nos últimos `dias`."""
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    dia = cast(Pedido.criado_em, Date)
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(dia, func.count(Pedido.id), func.sum(Pedido.valor))
            .where(Pedido.status == StatusPedido.pago, Pedido.criado_em >= desde)
            .group_by(dia)
            .order_by(dia)
        )
        return [
            {"_id": data.strftime("%Y-%m-%d"), "quantidade": quantidade, "total": float(total or 0)}
            for data, quantidade, total in resultado.all()
        ]
