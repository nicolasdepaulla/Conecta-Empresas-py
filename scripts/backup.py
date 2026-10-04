"""
Faz backup do banco Postgres via `pg_dump`, no formato "custom" (-Fc) --
já vem comprimido, e permite restaurar tabela por tabela se precisar,
diferente de um dump SQL puro.

Substitui o backup manual que existia no MongoDB (mongodump): lê a conexão
direto de DATABASE_URL (app/core/config.py), então não precisa configurar
nada além do que a aplicação já usa.

Requer o `pg_dump` instalado na máquina (vem junto com o Postgres, ou com
o pacote `postgresql-client`).

Rodar com: python -m scripts.backup

Pra restaurar um backup (sobrescreve o banco de destino):
    pg_restore -h localhost -p 5433 -U conecta -d conecta_empresas --clean --if-exists backups/arquivo.dump
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings

PASTA_BACKUPS = Path(__file__).resolve().parent.parent / "backups"


def _parse_database_url(database_url: str) -> dict:
    # urlparse não reconhece o "+asyncpg" no scheme -- tiramos só pra parsear.
    url_padrao = database_url.replace("postgresql+asyncpg://", "postgresql://")
    partes = urlparse(url_padrao)
    return {
        "usuario": partes.username,
        "senha": partes.password,
        "host": partes.hostname,
        "porta": partes.port or 5432,
        "banco": partes.path.lstrip("/"),
    }


def backup() -> Path:
    conexao = _parse_database_url(settings.database_url)
    PASTA_BACKUPS.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = PASTA_BACKUPS / f"backup_{conexao['banco']}_{timestamp}.dump"

    comando = [
        "pg_dump",
        "-h", conexao["host"],
        "-p", str(conexao["porta"]),
        "-U", conexao["usuario"],
        "-d", conexao["banco"],
        "-Fc",
        "-f", str(destino),
    ]

    ambiente = dict(os.environ)
    if conexao["senha"]:
        ambiente["PGPASSWORD"] = conexao["senha"]

    resultado = subprocess.run(comando, env=ambiente)
    if resultado.returncode != 0:
        print(
            "Backup falhou -- confira se o pg_dump está instalado "
            "(pacote postgresql-client) e se a conexão em DATABASE_URL está certa."
        )
        sys.exit(1)

    print(f"Backup criado em {destino}")
    return destino


if __name__ == "__main__":
    backup()
