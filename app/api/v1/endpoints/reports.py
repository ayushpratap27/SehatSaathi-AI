"""
Report management endpoints — Phase 7 (authenticated).

GET    /reports         — list user's reports
POST   /reports/upload  — upload + store report in DB
GET    /reports/{id}    — get report details
DELETE /reports/{id}    — soft-delete a report
GET    /reports/{id}/analysis    — get stored clinical analysis
GET    /reports/{id}/chat-history — get chat sessions
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.chat_repo import chat_message_repository, chat_session_repository
from app.schemas.dashboard import (
    ChatHistoryItem,
    ChatSessionResponse,
    ReportDetailResponse,
    ReportListResponse,
)
from app.schemas.auth import MessageResponse
from app.services.report_service import report_service
from app.utils.validators import validate_upload_file

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ReportListResponse, summary="List all my reports")
async def list_reports(
    limit:        int         = 20,
    offset:       int         = 0,
    current_user: User        = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> ReportListResponse:
    """Return a paginated list of the authenticated user's reports."""
    reports = await report_service.get_reports(db, current_user.id, limit=limit, offset=offset)
    from app.repositories.report_repo import report_repository  # noqa: PLC0415
    total   = await report_repository.count_by_user(db, current_user.id)
    return ReportListResponse(
        reports=[
            ReportDetailResponse(
                id=r.id,
                original_filename=r.original_filename,
                saved_filename=r.saved_filename,
                file_size=r.file_size,
                mime_type=r.mime_type,
                status=r.status,
                patient_name=r.patient_name,
                report_date=r.report_date,
                vector_index_path=r.vector_index_path,
                created_at=r.created_at.isoformat(),
            )
            for r in reports
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/upload",
    response_model=ReportDetailResponse,
    status_code=201,
    summary="Upload a new medical report",
)
async def upload_report(
    file:         UploadFile   = File(..., description="PDF or image medical report"),
    current_user: User         = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> ReportDetailResponse:
    """
    Upload a report, store it on disk, and create a database record.

    The record is linked to the authenticated user. Use the returned ``id``
    as ``document_id`` when calling ``/rag/index`` and ``/rag/chat``.
    """
    content = await validate_upload_file(file)
    report  = await report_service.create_report(db, current_user.id, file, content)
    return ReportDetailResponse(
        id=report.id,
        original_filename=report.original_filename,
        saved_filename=report.saved_filename,
        file_size=report.file_size,
        mime_type=report.mime_type,
        status=report.status,
        patient_name=report.patient_name,
        report_date=report.report_date,
        vector_index_path=report.vector_index_path,
        created_at=report.created_at.isoformat(),
    )


@router.get("/{report_id}", response_model=ReportDetailResponse, summary="Get report details")
async def get_report(
    report_id:    str,
    current_user: User        = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> ReportDetailResponse:
    """Return details of one report (ownership enforced)."""
    report = await report_service.get_report(db, report_id, current_user.id)
    return ReportDetailResponse(
        id=report.id,
        original_filename=report.original_filename,
        saved_filename=report.saved_filename,
        file_size=report.file_size,
        mime_type=report.mime_type,
        status=report.status,
        patient_name=report.patient_name,
        report_date=report.report_date,
        vector_index_path=report.vector_index_path,
        created_at=report.created_at.isoformat(),
    )


@router.delete("/{report_id}", response_model=MessageResponse, summary="Delete a report")
async def delete_report(
    report_id:    str,
    current_user: User        = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Soft-delete a report (marks is_deleted=True; data is not physically removed)."""
    await report_service.delete_report(db, report_id, current_user.id)
    return MessageResponse(message=f"Report '{report_id}' deleted.")


@router.get("/{report_id}/analysis", summary="Get stored clinical analysis")
async def get_analysis(
    report_id:    str,
    current_user: User        = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> dict:
    """Return the stored ReportAnalysis for a report (includes extracted text + JSON)."""
    analysis = await report_service.get_analysis(db, report_id, current_user.id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis stored for this report. Run /report/parse and /analysis/analyze first.",
        )
    return {
        "report_id":      analysis.report_id,
        "risk_level":     analysis.risk_level,
        "total_tests":    analysis.total_tests,
        "abnormal_count": analysis.abnormal_count,
        "critical_count": analysis.critical_count,
        "structured_json": analysis.structured_json,
        "analysis_json":   analysis.analysis_json,
        "summary_json":    analysis.summary_json,
    }


@router.get("/{report_id}/chat-history", response_model=list, summary="Get chat history")
async def get_chat_history(
    report_id:    str,
    current_user: User        = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> list:
    """Return all chat sessions and their messages for a report."""
    await report_service.get_report(db, report_id, current_user.id)  # ownership
    sessions = await chat_session_repository.get_by_report(db, report_id, current_user.id)
    result = []
    for session in sessions:
        messages_raw = await chat_message_repository.get_by_session(db, session.id)
        result.append(ChatSessionResponse(
            id=session.id,
            title=session.title,
            messages=[
                ChatHistoryItem(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    confidence=m.confidence,
                    created_at=str(m.created_at),
                )
                for m in messages_raw
            ],
            created_at=session.created_at.isoformat(),
        ).model_dump())
    return result
