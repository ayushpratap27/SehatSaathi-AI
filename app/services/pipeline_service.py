"""
Pipeline service — runs the full extraction + analysis + RAG indexing
pipeline in a background task after a report is uploaded.

Stages:
  1. Extract text (PyMuPDF / PaddleOCR)
  2. Parse to structured JSON (Phase 3 NER)
  3. Run clinical analysis (Phase 4 rules engine)
  4. Persist ReportAnalysis to database
  5. Index chunks into FAISS for RAG (Phase 6)
  6. Update report.status → "done"

Any failure updates status → "failed" so the user can see what happened.
"""

from __future__ import annotations

import logging

from app.models.report import ReportStatus

logger = logging.getLogger(__name__)


async def run_report_pipeline(report_id: str, file_path: str, original_filename: str) -> None:
    """
    Full async pipeline triggered as a FastAPI BackgroundTask after upload.

    Creates its own DB session since the request session closes before this runs.

    Args:
        report_id:         UUID of the Report record.
        file_path:         Absolute path to the saved file.
        original_filename: Original filename (for logging / metadata).
    """
    from app.database.session import AsyncSessionLocal  # noqa: PLC0415
    from app.repositories.report_repo import (  # noqa: PLC0415
        report_analysis_repository,
        report_repository,
    )

    async with AsyncSessionLocal() as db:
        try:
            # ── 1. Mark as processing ──────────────────────────────────── #
            await report_repository.update(db, report_id, status=ReportStatus.PROCESSING.value)
            await db.commit()
            logger.info("Pipeline [%s]: processing started", report_id[:8])

            # ── 2. Extract text ─────────────────────────────────────────── #
            from starlette.concurrency import run_in_threadpool  # noqa: PLC0415
            from app.services.document_service import document_service  # noqa: PLC0415
            from pathlib import Path  # noqa: PLC0415

            extraction = await run_in_threadpool(
                document_service.process, file_path, original_filename
            )
            logger.info(
                "Pipeline [%s]: extracted %d chars (scanned=%s)",
                report_id[:8], extraction.characters, extraction.is_scanned,
            )

            # ── 3. Parse to structured JSON ──────────────────────────────── #
            from ai.ner.json_builder import build_report  # noqa: PLC0415
            parsed = await run_in_threadpool(build_report, extraction.text)

            # ── 4. Run clinical analysis ─────────────────────────────────── #
            from ai.analysis.report_analyzer import report_analyzer  # noqa: PLC0415
            analysis = await run_in_threadpool(report_analyzer.analyze, parsed)
            logger.info(
                "Pipeline [%s]: risk=%s abnormal=%d critical=%d",
                report_id[:8], analysis.risk_level,
                analysis.analysis.abnormal, analysis.analysis.critical,
            )

            # ── 5. Persist analysis ─────────────────────────────────────── #
            existing = await report_analysis_repository.get_by_report(db, report_id)
            if existing:
                await report_analysis_repository.update(
                    db, existing.id,
                    extracted_text=extraction.text,
                    structured_json=parsed.model_dump_json(),
                    analysis_json=analysis.model_dump_json(),
                    risk_level=analysis.risk_level,
                    total_tests=analysis.analysis.total_tests,
                    abnormal_count=analysis.analysis.abnormal,
                    critical_count=analysis.analysis.critical,
                )
            else:
                await report_analysis_repository.create(
                    db,
                    report_id=report_id,
                    extracted_text=extraction.text,
                    structured_json=parsed.model_dump_json(),
                    analysis_json=analysis.model_dump_json(),
                    risk_level=analysis.risk_level,
                    total_tests=analysis.analysis.total_tests,
                    abnormal_count=analysis.analysis.abnormal,
                    critical_count=analysis.analysis.critical,
                )

            # ── 6. Index for RAG ─────────────────────────────────────────── #
            try:
                from ai.rag.chunker import document_chunker  # noqa: PLC0415
                from ai.rag.embedding_service import embedding_service  # noqa: PLC0415
                from ai.rag.vector_store import vector_store_manager  # noqa: PLC0415

                chunks = await run_in_threadpool(
                    document_chunker.chunk, extraction.text, original_filename, report_id
                )
                if chunks:
                    texts = [c.text for c in chunks]
                    embeddings = await run_in_threadpool(embedding_service.embed_documents, texts)
                    vector_store_manager.create(
                        document_id=report_id,
                        embeddings=embeddings,
                        chunks=chunks,
                        dimension=embedding_service.dimension,
                    )
                    # Save index path to report record
                    await report_repository.update(
                        db, report_id,
                        vector_index_path=f"data/vector_stores/{report_id}",
                    )
                    logger.info("Pipeline [%s]: %d chunks indexed for RAG", report_id[:8], len(chunks))
            except Exception as rag_exc:
                # RAG indexing is optional — don't fail the whole pipeline
                logger.warning("Pipeline [%s]: RAG indexing failed (non-fatal): %s", report_id[:8], rag_exc)

            # ── 7. Mark as done ──────────────────────────────────────────── #
            patient_name = parsed.patient.name if parsed.patient else None
            report_date  = parsed.report_date

            await report_repository.update(
                db, report_id,
                status=ReportStatus.DONE.value,
                patient_name=patient_name,
                report_date=report_date,
            )
            await db.commit()
            logger.info("Pipeline [%s]: DONE ✓", report_id[:8])

        except Exception as exc:
            logger.exception("Pipeline [%s]: FAILED — %s", report_id[:8], exc)
            try:
                await report_repository.update(db, report_id, status=ReportStatus.FAILED.value)
                await db.commit()
            except Exception:
                pass
