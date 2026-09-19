from datetime import datetime, timezone
from fastapi import HTTPException
from app.repositories import pedido_repository, pacote_repository
from app.services import mercadopago_service


async def criar_pedido_para_checkout(username: str, slug_pacote: str) -> dict:
    """Cria o pedido (status 'pendente') e a cobrança real no Mercado Pago."""
    pacote = await pacote_repository.buscar_por_slug(slug_pacote)
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")

    pedido = {
        "username": username,
        "pacote_id": str(pacote["_id"]),
        "pacote_nome": pacote["nome"],
        "valor": pacote["preco"],
        "status": "pendente",
        "criado_em": datetime.now(timezone.utc),
    }
    pedido_id = await pedido_repository.criar_pedido(pedido)

    cobranca = await mercadopago_service.criar_ordem_de_pagamento(
        pedido_id=pedido_id, valor=pacote["preco"], descricao=pacote["nome"]
    )

    return {
        "pedido_id": pedido_id,
        "valor": pacote["preco"],
        "status": "pendente",
        "checkout_url": cobranca["checkout_url"],
    }


async def confirmar_pagamento_por_id(payment_id: str):
    """
    Chamado pelo webhook. Busca o pagamento no Mercado Pago pra descobrir
    qual pedido nosso ele representa (via external_reference) e o status real.
    """
    pagamento = await mercadopago_service.buscar_pagamento_por_id(payment_id)
    pedido_id = pagamento.get("external_reference")
    status_mp = pagamento.get("status")  # approved, pending, rejected, cancelled...

    if not pedido_id:
        raise HTTPException(status_code=400, detail="Pagamento sem external_reference.")

    if status_mp == "approved":
        await pedido_repository.atualizar_status(pedido_id, "pago")
    elif status_mp in ("rejected", "cancelled"):
        await pedido_repository.atualizar_status(pedido_id, "cancelado")

    return {"success": True, "pedido_id": pedido_id, "status_mp": status_mp}


async def historico_do_usuario(username: str):
    return await pedido_repository.listar_por_usuario(username)