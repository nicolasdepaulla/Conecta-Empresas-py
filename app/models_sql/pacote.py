"""
Model SQL (Postgres) do pacote -- espelha app/models/pacote.py (Mongo).
sessao_id agora é uma FOREIGN KEY de verdade: o banco rejeita criar um
pacote apontando pra uma sessão que não existe (no Mongo isso dependia só
do código tomar cuidado).
"""
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.postgres import Base


class Pacote(Base):
    __tablename__ = "pacotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    setor: Mapped[str] = mapped_column(String(100), nullable=False)
    # Numeric (não Float) -- valor monetário não deve sofrer arredondamento
    # de ponto flutuante.
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade_contatos: Mapped[int] = mapped_column(Integer, nullable=False)
    imagem: Mapped[str] = mapped_column(String(255), nullable=False)
    cobrar_id: Mapped[str] = mapped_column(String(50), nullable=False)

    sessao_id: Mapped[int] = mapped_column(ForeignKey("sessoes.id"), nullable=False)
    sessao: Mapped["Sessao"] = relationship(back_populates="pacotes")

    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="pacote")
