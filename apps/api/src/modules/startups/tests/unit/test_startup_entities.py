"""Testes das entidades do modulo startups."""

from uuid import uuid4

import pytest

from apps.api.src.modules.startups.domain.entities import Startup, StartupEvidence
from apps.api.src.modules.startups.domain.enums import StartupEvidenceType
from apps.api.src.modules.startups.domain.exceptions import InvalidStartupDataError


def test_startup_normalizes_basic_fields() -> None:
    startup = Startup(
        name="  Acme AI  ",
        website_url=" https://acme.example.com ",
        sector=" AI Infra ",
        country=" BR ",
    )

    assert startup.name == "Acme AI"
    assert startup.website_url == "https://acme.example.com"
    assert startup.sector == "AI Infra"
    assert startup.country == "BR"


def test_startup_requires_name() -> None:
    with pytest.raises(InvalidStartupDataError):
        Startup(name=" ")


def test_update_changes_fields_and_timestamp() -> None:
    startup = Startup(name="Old")
    previous_updated_at = startup.updated_at

    startup.update(name="New", description=" nova descricao ")

    assert startup.name == "New"
    assert startup.description == "nova descricao"
    assert startup.updated_at >= previous_updated_at


def test_evidence_requires_source_url() -> None:
    with pytest.raises(InvalidStartupDataError):
        StartupEvidence(
            startup_id=uuid4(),
            scraping_result_id=uuid4(),
            source_url=" ",
        )


def test_evidence_validates_confidence_score() -> None:
    with pytest.raises(InvalidStartupDataError):
        StartupEvidence(
            startup_id=uuid4(),
            scraping_result_id=uuid4(),
            source_url="https://example.com",
            confidence_score=1.2,
        )


def test_evidence_defaults_type_to_other() -> None:
    evidence = StartupEvidence(
        startup_id=uuid4(),
        scraping_result_id=uuid4(),
        source_url="https://example.com",
    )

    assert evidence.evidence_type is StartupEvidenceType.OTHER
