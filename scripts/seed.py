"""
Popula o Postgres com os dados reais extraídos do projeto Node.js original,
substituindo os 9 arquivos HTML estáticos duplicados por registros
referenciados (pacotes -> sessoes, via FOREIGN KEY de verdade).

Correções aplicadas em relação ao original:
- Turismo/Petshop/Fitness tinham preço R$ 1000 mas apontavam pro checkout de
  R$ 130 (cobrar_id errado). Agora usam a faixa "140", seguindo a mesma lógica
  sequencial das demais (100/110/120/130), até a integração de pagamento real
  definir os valores/planos definitivos.
- Imagem genérica (login.jpeg) repetida nos 9 pacotes -> usar imagem própria
  por pacote assim que as fotos definitivas forem enviadas.

Rodar com: python -m scripts.seed
"""
import asyncio
from sqlalchemy import delete
from app.core.postgres import AsyncSessionLocal
from app.models_sql.pacote import Pacote
from app.models_sql.sessao import Sessao
from app.repositories import pacote_repository, sessao_repository

SESSAO_CONTATO_EMPRESARIAL = {
    "titulo": "Dados de Contato Empresarial",
    "itens": ["Número de Telefone", "Email Corporativo", "CNPJ"],
}

PACOTES = [
    {"slug": "imobiliario", "nome": "Pacote Premium Imobiliário", "setor": "Imobiliário",
     "preco": 100.00, "quantidade_contatos": 100, "cobrar_id": "100", "imagem": "img/login.jpeg"},
    {"slug": "automotivo", "nome": "Pacote Premium Automotivo", "setor": "Automotivo",
     "preco": 100.00, "quantidade_contatos": 100, "cobrar_id": "100", "imagem": "img/login.jpeg"},
    {"slug": "agro", "nome": "Pacote Premium Agro", "setor": "Agro",
     "preco": 100.00, "quantidade_contatos": 100, "cobrar_id": "100", "imagem": "img/login.jpeg"},
    {"slug": "beleza-cosmeticos", "nome": "Pacote Premium Beleza-Cosméticos", "setor": "Beleza e Cosméticos",
     "preco": 120.00, "quantidade_contatos": 120, "cobrar_id": "120", "imagem": "img/login.jpeg"},
    {"slug": "construcao", "nome": "Pacote Premium Construção", "setor": "Construção",
     "preco": 110.00, "quantidade_contatos": 110, "cobrar_id": "110", "imagem": "img/login.jpeg"},
    {"slug": "tecnologia", "nome": "Pacote Premium Tecnologia", "setor": "Tecnologia",
     "preco": 130.00, "quantidade_contatos": 130, "cobrar_id": "130", "imagem": "img/login.jpeg"},
    {"slug": "turismo-hotelaria", "nome": "Pacote Turismo e Hotelaria", "setor": "Turismo e Hotelaria",
     "preco": 1000.00, "quantidade_contatos": 1000, "cobrar_id": "140", "imagem": "img/login.jpeg"},
    {"slug": "petshop", "nome": "Pacote Petshop", "setor": "Petshop",
     "preco": 1000.00, "quantidade_contatos": 1000, "cobrar_id": "140", "imagem": "img/login.jpeg"},
    {"slug": "fitness", "nome": "Pacote Fitness", "setor": "Fitness",
     "preco": 1000.00, "quantidade_contatos": 1000, "cobrar_id": "140", "imagem": "img/login.jpeg"},
]


async def seed():
    # Apaga na ordem que respeita a FK (pacotes referencia sessoes).
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Pacote))
        await session.execute(delete(Sessao))
        await session.commit()

    sessao_id = await sessao_repository.criar_sessao(
        SESSAO_CONTATO_EMPRESARIAL["titulo"], SESSAO_CONTATO_EMPRESARIAL["itens"]
    )

    for pacote in PACOTES:
        pacote["sessao_id"] = sessao_id
        await pacote_repository.criar_pacote(pacote)

    print(f"{len(PACOTES)} pacotes inseridos, referenciando 1 sessão compartilhada.")


if __name__ == "__main__":
    asyncio.run(seed())
