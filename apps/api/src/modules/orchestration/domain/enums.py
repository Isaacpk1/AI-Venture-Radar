"""Enums do modulo orchestration."""

from enum import StrEnum


class AnalysisJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UrlIngestionJobStatus(StrEnum):
    """Estado da maquina de estados que leva uma URL bruta ate chunks
    embeddados (Orchestration V2)."""

    PENDING = "pending"
    SCRAPING = "scraping"
    INGESTING = "ingesting"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"
