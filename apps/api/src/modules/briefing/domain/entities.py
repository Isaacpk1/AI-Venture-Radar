"""Entidades do dominio do modulo briefing."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from apps.api.src.modules.briefing.domain.exceptions import BriefingError


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Briefing:
    """Briefing executivo em Markdown gerado para uma startup."""

    startup_id: UUID
    content: str

    id: UUID = field(default_factory=uuid4)
    generated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.content = self.content.strip()
        if not self.content:
            raise BriefingError("Briefing precisa ter conteudo.")

    def update_content(self, content: str) -> None:
        """Substitui o conteudo (ex: prosa reescrita pelo Briefing Agent)."""

        content = content.strip()
        if not content:
            raise BriefingError("Briefing precisa ter conteudo.")
        self.content = content
