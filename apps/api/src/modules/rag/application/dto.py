"""DTOs do modulo RAG."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class SearchEvidenceInput:
    query: str
    limit: int = 5


@dataclass
class EvidenceChunkView:
    chunk_id: UUID
    document_id: UUID
    source_url: str
    text: str
    score: float


@dataclass
class SearchEvidenceView:
    query: str
    results: list[EvidenceChunkView]


@dataclass
class GenerateRagAnswerInput:
    query: str
    evidences: list[EvidenceChunkView]


@dataclass
class RagCitationView:
    chunk_id: UUID
    document_id: UUID
    source_url: str
    quote: str


@dataclass
class RagAnswerView:
    query: str
    answer: str
    citations: list[RagCitationView]
    evidences: list[EvidenceChunkView]


@dataclass
class AnswerQuestionInput:
    query: str
    limit: int = 5
