"""Enums do modulo startup_discovery."""

from enum import Enum


class DiscoveryRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
