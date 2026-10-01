"""
Model SQL (Postgres) da sessão -- espelha app/models/sessao.py (Mongo).
Bloco de conteúdo reutilizável entre pacotes (ex.: "Dados de Contato
Empresarial"), pra não repetir o mesmo texto em cada pacote.
"""
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.postgres import Base


class Sessao(Base):
    __tablename__ = "sessoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    itens: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)

    pacotes: Mapped[list["Pacote"]] = relationship(back_populates="sessao")
