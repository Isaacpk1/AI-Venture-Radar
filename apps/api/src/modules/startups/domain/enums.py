"""Enums do modulo startups."""

from enum import Enum


class StartupEvidenceType(str, Enum):
    WEBSITE = "website"
    NEWS = "news"
    BLOG = "blog"
    DOCUMENTATION = "documentation"
    OTHER = "other"
