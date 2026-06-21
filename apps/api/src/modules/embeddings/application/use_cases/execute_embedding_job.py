"""Caso de uso executado pelo embedding_worker."""

from time import perf_counter
from uuid import UUID

from apps.api.src.modules.embeddings.application.dto import UpsertChunkEmbeddingInput
from apps.api.src.modules.embeddings.application.ports import ChunkSourceReader
from apps.api.src.modules.embeddings.application.unit_of_work import (
    EmbeddingsUnitOfWorkFactory,
)
from apps.api.src.modules.embeddings.application.use_cases.upsert_chunk_embedding import (
    UpsertChunkEmbedding,
)
from apps.api.src.modules.embeddings.domain.entities import (
    EmbeddingJobChunk,
    chunk_content_hash,
    estimate_input_tokens,
)
from apps.api.src.modules.embeddings.domain.enums import (
    EmbeddingJobChunkStatus,
    EmbeddingJobStatus,
)
from apps.api.src.modules.embeddings.domain.exceptions import (
    EmbeddingJobNotFoundError,
    EmbeddingJobPartiallyFailedError,
)


class ExecuteEmbeddingJob:
    """Gera e persiste o embedding de todos os chunks de um documento.

    Idempotente: jobs ja finalizados (COMPLETED/PARTIAL/FAILED) sao no-op.
    Jobs RUNNING retomam apenas os chunks ainda PENDING — a fila entrega
    "pelo menos uma vez", entao a mesma mensagem pode chegar de novo apos
    um crash no meio do lote.
    """

    def __init__(
        self,
        *,
        uow_factory: EmbeddingsUnitOfWorkFactory,
        chunk_source_reader: ChunkSourceReader,
        upsert_chunk_embedding: UpsertChunkEmbedding,
    ) -> None:
        self._uow_factory = uow_factory
        self._chunk_source_reader = chunk_source_reader
        self._upsert_chunk_embedding = upsert_chunk_embedding

    async def execute(self, *, job_id: UUID) -> None:
        async with self._uow_factory() as uow:
            job = await uow.job_repository.get_by_id(job_id)
            if job is None:
                raise EmbeddingJobNotFoundError(f"EmbeddingJob {job_id} nao encontrado.")

            if job.status not in (EmbeddingJobStatus.PENDING, EmbeddingJobStatus.RUNNING):
                return

            chunks = await self._chunk_source_reader.list_chunks(job.document_id)

            if job.status is EmbeddingJobStatus.PENDING:
                if not chunks:
                    job.fail("Documento sem chunks para gerar embedding.")
                    await uow.job_repository.save(job)
                    await uow.commit()
                    return

                job.start(total_chunks=len(chunks))
                chunk_rows = [
                    EmbeddingJobChunk(job_id=job.id, chunk_id=chunk.chunk_id)
                    for chunk in chunks
                ]
                await uow.job_repository.save(job)
                for row in chunk_rows:
                    await uow.job_chunk_repository.save(row)
                await uow.commit()
            else:
                chunk_rows = await uow.job_chunk_repository.list_by_job_id(job.id)

        chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        pending_rows = [
            row for row in chunk_rows if row.status is EmbeddingJobChunkStatus.PENDING
        ]

        for row in pending_rows:
            try:
                chunk = chunks_by_id.get(row.chunk_id)
                if chunk is None:
                    raise EmbeddingJobNotFoundError(
                        f"Chunk {row.chunk_id} nao encontrado para o documento {job.document_id}."
                    )
                started_at = perf_counter()
                view = await self._upsert_chunk_embedding.execute(
                    UpsertChunkEmbeddingInput(
                        chunk_id=chunk.chunk_id,
                        document_id=job.document_id,
                        source_url=chunk.source_url,
                        text=chunk.text,
                    )
                )
                latency_ms = max(0, int((perf_counter() - started_at) * 1000))
                row.complete(
                    model_name=view.model_name,
                    vector_dimension=view.dimension,
                    input_char_count=len(chunk.text),
                    estimated_input_tokens=estimate_input_tokens(chunk.text),
                    latency_ms=latency_ms,
                    content_hash=chunk_content_hash(chunk.text),
                )
            except Exception as exc:
                row.record_failure(f"{type(exc).__name__}: {exc}")

            async with self._uow_factory() as uow:
                await uow.job_chunk_repository.save(row)
                await uow.commit()

        async with self._uow_factory() as uow:
            all_rows = await uow.job_chunk_repository.list_by_job_id(job.id)
            still_pending = [
                row for row in all_rows if row.status is EmbeddingJobChunkStatus.PENDING
            ]
            if still_pending:
                raise EmbeddingJobPartiallyFailedError(
                    f"EmbeddingJob {job.id} ainda tem {len(still_pending)} "
                    "chunk(s) pendentes; sera reentregue."
                )

            succeeded = sum(
                1 for row in all_rows if row.status is EmbeddingJobChunkStatus.COMPLETED
            )
            failed = sum(
                1 for row in all_rows if row.status is EmbeddingJobChunkStatus.FAILED
            )
            refreshed_job = await uow.job_repository.get_by_id(job.id)
            refreshed_job.record_metrics_from_chunks(all_rows)
            refreshed_job.finish(succeeded=succeeded, failed=failed)
            await uow.job_repository.save(refreshed_job)
            await uow.commit()
