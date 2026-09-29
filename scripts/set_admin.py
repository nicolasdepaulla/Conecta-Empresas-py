"""
Marca um usuário existente como administrador (is_admin=True), liberando
acesso ao dashboard administrativo de vendas (GET /admin/dashboard).

Rodar com: python -m scripts.set_admin <username>
"""
import asyncio
import sys
from app.repositories import usuario_repository


async def set_admin(username: str):
    usuario = await usuario_repository.buscar_por_username(username)
    if not usuario:
        print(f"Usuário '{username}' não encontrado.")
        return

    await usuario_repository.marcar_como_admin(username)
    print(f"Usuário '{username}' agora é administrador.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m scripts.set_admin <username>")
        sys.exit(1)

    asyncio.run(set_admin(sys.argv[1]))
