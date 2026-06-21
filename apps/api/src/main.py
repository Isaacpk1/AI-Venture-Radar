"""Ponto de entrada HTTP da aplicacao."""

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from apps.api.src.database.relational.session import check_database_connection
from apps.api.src.shared.queue.dramatiq_broker import (
    check_redis_connection,
)
from apps.api.src.modules.agents.presentation.routes import (
    router as agents_router,
)
from apps.api.src.modules.ingestion.presentation.routes import (
    router as ingestion_router,
)
from apps.api.src.modules.scraping.presentation.routes import (
    router as scraping_router,
)


app = FastAPI(
    title="NVIDIA Startup AI Radar",
    version="0.1.0",
    description="API para coleta e analise de dados publicos de startups.",
)


async def get_dependency_health() -> dict[str, bool]:
    """Consulta dependencias sem deixar uma falha esconder a outra."""

    results = await asyncio.gather(
        check_database_connection(),
        check_redis_connection(),
        return_exceptions=True,
    )

    return {
        "postgres": results[0] is True,
        "redis": results[1] is True,
    }


@app.get("/health", tags=["system"])
async def health_check() -> JSONResponse:
    """Informa se API, PostgreSQL e Redis estao prontos para uso."""

    dependencies = await get_dependency_health()
    is_healthy = all(dependencies.values())

    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "ok" if is_healthy else "degraded",
            "dependencies": dependencies,
        },
    )


# Cada modulo expoe seu proprio router. O main apenas conecta esses routers a
# aplicacao global, sem conhecer regras internas de scraping.
app.include_router(scraping_router)
app.include_router(agents_router)
app.include_router(ingestion_router)
