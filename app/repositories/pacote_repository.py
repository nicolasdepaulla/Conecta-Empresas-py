"""
Repository de pacotes -- migrado de MongoDB pra Postgres (SQLAlchemy
async). O JOIN com sessoes, que era um $lookup+$unwind no Mongo, agora é
uma FOREIGN KEY de verdade (pacotes.sessao_id -> sessoes.id) resolvida com
joinedload. Mantém os mesmos nomes de função e o retorno em dict (com
"_id" e "sessao" aninhado), que é o formato que o router já espera.
"""
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.core.postgres import AsyncSessionLocal
from app.models_sql.pacote import Pacote


def _to_dict(pacote: Pacote | None) -> dict | None:
    if pacote is None:
        return None
    return {
        "_id": pacote.id,
        "slug": pacote.slug,
        "nome": pacote.nome,
        "setor": pacote.setor,
        # preco vem como Decimal do Postgres (coluna Numeric) -- convertido
        # pra float aqui, igual ao Mongo, pra quem consome não precisar mudar.
        "preco": float(pacote.preco),
        "quantidade_contatos": pacote.quantidade_contatos,
        "imagem": pacote.imagem,
        "cobrar_id": pacote.cobrar_id,
        "sessao_id": pacote.sessao_id,
        "sessao": {
            "_id": pacote.sessao.id,
            "titulo": pacote.sessao.titulo,
            "itens": list(pacote.sessao.itens),
        },
    }


async def listar_pacotes() -> list[dict]:
    """Lista todos os pacotes já com a sessão resolvida (era um $lookup no Mongo)."""
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(select(Pacote).options(joinedload(Pacote.sessao)))
        return [_to_dict(p) for p in resultado.scalars().all()]


async def buscar_por_slug(slug: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(Pacote).options(joinedload(Pacote.sessao)).where(Pacote.slug == slug)
        )
        return _to_dict(resultado.scalar_one_or_none())


async def criar_pacote(pacote: dict) -> str:
    async with AsyncSessionLocal() as session:
        novo = Pacote(
            slug=pacote["slug"],
            nome=pacote["nome"],
            setor=pacote["setor"],
            preco=pacote["preco"],
            quantidade_contatos=pacote["quantidade_contatos"],
            imagem=pacote["imagem"],
            cobrar_id=pacote["cobrar_id"],
            sessao_id=int(pacote["sessao_id"]),
        )
        session.add(novo)
        await session.commit()
        await session.refresh(novo)
        return str(novo.id)
