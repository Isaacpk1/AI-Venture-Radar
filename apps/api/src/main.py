"""Ponto de entrada HTTP da aplicação."""

from fastapi import FastAPI

from apps.api.src.modules.scraping.presentation.routes import (
    router as scraping_router,
)


app = FastAPI(
    title="NVIDIA Startup AI Radar",
    version="0.1.0",
    description="API para coleta e análise de dados públicos de startups.",
)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Informa se o processo da API está disponível."""

    return {"status": "ok"}


# Cada módulo expõe seu próprio router. O main apenas conecta esses routers à
# aplicação global, sem conhecer regras internas de scraping.
app.include_router(scraping_router)
