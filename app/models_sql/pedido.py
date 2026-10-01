"""
Model SQL (Postgres) do pedido -- espelha app/models/pedido.py (Mongo).

Duas diferenças de propósito em relação à versão Mongo:
- usuario_id/pacote_id são FOREIGN KEY de verdade (pedidos.pacote_id ->
  pacotes.id, conforme a issue de migração).
- status é um ENUM nativo do Postgres (reaproveitando o mesmo StatusPedido
  já usado no lado Mongo, pra não duplicar o vocabulário de status em dois
  lugares) -- o banco rejeita qualquer valor fora de
  pendente/pago/cancelado, em vez de confiar só no código da aplicação.

pacote_nome e valor continuam existindo como "retrato" do momento da
compra (snapshot) -- assim o pedido não muda de cara se o pacote for
renomeado ou tiver o preço alterado depois.
"""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.postgres import Base
from app.models.pedido import StatusPedido


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    pacote_id: Mapped[int] = mapped_column(ForeignKey("pacotes.id"), nullable=False)

    pacote_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[StatusPedido] = mapped_column(
        SAEnum(StatusPedido, name="status_pedido", values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=StatusPedido.pendente,
        server_default=StatusPedido.pendente.value,
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="pedidos")
    pacote: Mapped["Pacote"] = relationship(back_populates="pedidos")
