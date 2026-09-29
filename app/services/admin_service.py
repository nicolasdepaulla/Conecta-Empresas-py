"""
Monta o payload do dashboard administrativo de vendas, combinando as
agregações de app/repositories/pedido_repository.py num único retorno
pro front-end (public/dashboard.html).
"""
from app.repositories import pedido_repository


async def obter_dashboard():
    resumo = await pedido_repository.resumo_por_status()
    por_pacote = await pedido_repository.vendas_por_pacote()
    por_dia = await pedido_repository.vendas_por_dia()

    total_vendido = sum(item["total"] for item in resumo if item["_id"] == "pago")
    pedidos_pagos = sum(item["quantidade"] for item in resumo if item["_id"] == "pago")
    ticket_medio = (total_vendido / pedidos_pagos) if pedidos_pagos else 0.0

    return {
        "total_vendido": round(total_vendido, 2),
        "ticket_medio": round(ticket_medio, 2),
        "pedidos_pagos": pedidos_pagos,
        "resumo_por_status": [
            {"status": item["_id"], "quantidade": item["quantidade"], "total": round(item["total"], 2)}
            for item in resumo
        ],
        "vendas_por_pacote": [
            {"pacote": item["_id"], "quantidade": item["quantidade"], "total": round(item["total"], 2)}
            for item in por_pacote
        ],
        "vendas_por_dia": [
            {"data": item["_id"], "quantidade": item["quantidade"], "total": round(item["total"], 2)}
            for item in por_dia
        ],
    }
