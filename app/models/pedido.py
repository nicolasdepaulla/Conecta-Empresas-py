from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum


class StatusPedido(str, Enum):
    pendente = "pendente"
    pago = "pago"
    cancelado = "cancelado"


class Pedido(BaseModel):
    username: str
    pacote_id: str
    pacote_nome: str
    valor: float
    status: StatusPedido = StatusPedido.pendente
    criado_em: datetime = datetime.now(timezone.utc)
