"""
Dashboard service — aggregates statistics for the authenticated user.
"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import ReportStatus
from app.repositories.report_repo import report_repository
from app.schemas.dashboard import DashboardResponse, RecentReport

logger = logging.getLogger(__name__)


class DashboardService:
    """Computes dashboard statistics for a single user."""

    async def get_dashboard(
        self, db: AsyncSession, user_id: str
    ) -> DashboardResponse:
        total         = await report_repository.count_by_user(db, user_id)
        this_month    = await report_repository.count_this_month(db, user_id)
        recent_raw    = await report_repository.get_by_user(db, user_id, limit=5)

        # Count completed analyses
        completed = sum(
            1 for r in await report_repository.get_by_user(db, user_id, limit=1000)
            if r.status == ReportStatus.DONE.value
        )

        recent: List[RecentReport] = [
            RecentReport(
                id=r.id,
                original_filename=r.original_filename,
                status=r.status,
                patient_name=r.patient_name,
                risk_level=r.analysis.risk_level if r.analysis else None,
                created_at=r.created_at.isoformat(),
            )
            for r in recent_raw
        ]

        return DashboardResponse(
            total_reports=total,
            reports_this_month=this_month,
            completed_analyses=completed,
            recent_reports=recent,
        )


dashboard_service = DashboardService()
