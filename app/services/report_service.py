"""
Report history service — persists and retrieves uploaded report records.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportStatus
from app.repositories.report_repo import report_analysis_repository, report_repository
from app.utils.file_manager import generate_unique_filename, save_file
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ReportService:
    """Manages the lifecycle of uploaded medical reports."""

    async def create_report(
        self,
        db:         AsyncSession,
        user_id:    str,
        file:       UploadFile,
        content:    bytes,
    ) -> Report:
        """Save an uploaded file to disk and create a DB record."""
        import os  # noqa: PLC0415
        original_filename = file.filename or "unknown"
        saved_filename    = generate_unique_filename(original_filename)

        # Always use an absolute path so the record works regardless of the
        # server's working directory at the time it was started.
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        file_path  = save_file(content, upload_dir, saved_filename)

        report = await report_repository.create(
            db,
            user_id=user_id,
            original_filename=original_filename,
            saved_filename=saved_filename,
            file_path=str(file_path),
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            status=ReportStatus.PENDING.value,
        )
        logger.info("Report created: id=%s user=%s file=%s", report.id, user_id, original_filename)
        return report

    async def get_reports(
        self,
        db:      AsyncSession,
        user_id: str,
        limit:   int = 20,
        offset:  int = 0,
    ) -> List[Report]:
        return await report_repository.get_by_user(db, user_id, limit=limit, offset=offset)

    async def get_report(
        self, db: AsyncSession, report_id: str, user_id: str
    ) -> Report:
        report = await report_repository.get_user_report(db, report_id, user_id)
        if not report:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Report '{report_id}' not found.")
        return report

    async def delete_report(
        self, db: AsyncSession, report_id: str, user_id: str
    ) -> None:
        deleted = await report_repository.soft_delete(db, report_id, user_id)
        if not deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Report '{report_id}' not found.")
        logger.info("Report soft-deleted: id=%s user=%s", report_id, user_id)

    async def update_status(
        self, db: AsyncSession, report_id: str, new_status: ReportStatus, **kwargs
    ) -> Optional[Report]:
        return await report_repository.update(db, report_id, status=new_status.value, **kwargs)

    async def get_analysis(self, db: AsyncSession, report_id: str, user_id: str):
        await self.get_report(db, report_id, user_id)  # ownership check
        return await report_analysis_repository.get_by_report(db, report_id)


report_service = ReportService()
