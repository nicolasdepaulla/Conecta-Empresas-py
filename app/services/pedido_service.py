from datetime import datetime, timezone
from fastapi import HTTPException
from app.repositories import pedido_repository, pacote_repository, usuario_repository
from app.services import mercadopago_service


async def criar_pedido_para_checkout(username: str, slug_pacote: str) -> dict:
    """Cria o pedido (status 'pendente') e a cobrança real no Mercado Pago."""
    pacote = await pacote_repository.buscar_por_slug(slug_pacote)
    if not pacote:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")

    usuario = await usuario_repository.buscar_por_username(username)
    email_comprador = usuario.get("email") if usuario else None

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
        pedido_id=pedido_id,
        valor=pacote["preco"],
        descricao=pacote["nome"],
        email_comprador=email_comprador,
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

    Trata dois casos que uma notificação de webhook pode disparar mais de
    uma vez (retry do Mercado Pago) ou apontar para um pedido inválido:
    - pedido_id que não existe na nossa base -> 404
    - pedido que já está "pago" -> não reprocessa (idempotência)
    """
    pagamento = await mercadopago_service.buscar_pagamento_por_id(payment_id)
    pedido_id = pagamento.get("external_reference")
    status_mp = pagamento.get("status")  # approved, pending, rejected, cancelled...

    if not pedido_id:
        raise HTTPException(status_code=400, detail="Pagamento sem external_reference.")

    pedido = await pedido_repository.buscar_por_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado para este pagamento.")

    if pedido.get("status") == "pago":
        return {"success": True, "pedido_id": pedido_id, "status_mp": status_mp, "ja_processado": True}

    if status_mp == "approved":
        await pedido_repository.atualizar_status(pedido_id, "pago")
    elif status_mp in ("rejected", "cancelled"):
        await pedido_repository.atualizar_status(pedido_id, "cancelado")

    return {"success": True, "pedido_id": pedido_id, "status_mp": status_mp}


async def historico_do_usuario(username: str):
    pedidos = await pedido_repository.listar_por_usuario(username)
    for p in pedidos:
        p["_id"] = str(p["_id"])
    return pedidos