"""Report and ReportAnalysis repositories."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportAnalysis, ReportStatus
from app.repositories.base_repo import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Report]:
        result = await db.execute(
            select(Report)
            .where(and_(Report.user_id == user_id, Report.is_deleted == False))  # noqa: E712
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_user_report(
        self, db: AsyncSession, report_id: str, user_id: str
    ) -> Optional[Report]:
        """Fetch a report only if it belongs to ``user_id`` (ownership check)."""
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.user_id == user_id,
                    Report.is_deleted == False,  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def soft_delete(
        self, db: AsyncSession, report_id: str, user_id: str
    ) -> bool:
        report = await self.get_user_report(db, report_id, user_id)
        if not report:
            return False
        report.is_deleted = True
        await db.flush()
        return True

    async def count_by_user(self, db: AsyncSession, user_id: str) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Report)
            .where(and_(Report.user_id == user_id, Report.is_deleted == False))  # noqa: E712
        )
        return result.scalar_one()

    async def count_this_month(self, db: AsyncSession, user_id: str) -> int:
        from sqlalchemy import extract  # noqa: PLC0415
        from datetime import datetime  # noqa: PLC0415
        now = datetime.utcnow()
        result = await db.execute(
            select(func.count())
            .select_from(Report)
            .where(
                and_(
                    Report.user_id == user_id,
                    Report.is_deleted == False,  # noqa: E712
                    extract("year",  Report.created_at) == now.year,
                    extract("month", Report.created_at) == now.month,
                )
            )
        )
        return result.scalar_one()


class ReportAnalysisRepository(BaseRepository[ReportAnalysis]):
    model = ReportAnalysis

    async def get_by_report(
        self, db: AsyncSession, report_id: str
    ) -> Optional[ReportAnalysis]:
        result = await db.execute(
            select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
        )
        return result.scalar_one_or_none()


report_repository          = ReportRepository()
report_analysis_repository = ReportAnalysisRepository()
