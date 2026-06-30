"""Exporta as analises (startups, recomendacoes, briefings, evidencias) do
Postgres local para um JSON que pode ser inspecionado.

Rode na raiz do projeto, com o venv ativo:

    venv\\Scripts\\python.exe export_analyses.py

Gera: analyses_export.json (na raiz). Sem dados sensiveis alem do que ja
esta no proprio banco. Pode apagar o arquivo e este script depois.
"""

import asyncio
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "analyses_export.json"

TABLES = [
    "startups",
    "recommendations",
    "briefings",
    "startup_evidences",
    "url_ingestion_jobs",
]


def _load_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not url:
        raise SystemExit("DATABASE_URL nao encontrada (.env ou env var).")
    # asyncpg.connect nao aceita o sufixo de driver do SQLAlchemy
    url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    url = re.sub(r"^postgresql\+psycopg2://", "postgresql://", url)
    return url


def _jsonable(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


async def main() -> None:
    try:
        import asyncpg
    except ImportError:
        raise SystemExit(
            "asyncpg nao instalado no venv. Rode: pip install asyncpg"
        )

    url = _load_database_url()
    conn = await asyncpg.connect(url)
    export: dict[str, object] = {}

    # quais tabelas existem de fato
    existing = {
        r["table_name"]
        for r in await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )
    }

    for table in TABLES:
        if table not in existing:
            export[table] = {"_note": "tabela inexistente"}
            continue
        rows = await conn.fetch(f"SELECT * FROM {table}")
        export[table] = {
            "count": len(rows),
            "rows": [
                {k: _jsonable(v) for k, v in dict(r).items()} for r in rows
            ],
        }
        print(f"{table}: {len(rows)} linhas")

    await conn.close()
    OUTPUT.write_text(
        json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nOK -> {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
