"""
Dashboard endpoint — Phase 7 (authenticated).

GET /dashboard — aggregated statistics for the authenticated user.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Get user dashboard",
    description=(
        "Returns aggregated statistics for the authenticated user: total reports, "
        "reports uploaded this month, completed analyses, and the 5 most recent reports."
    ),
)
async def get_dashboard(
    current_user: User        = Depends(get_current_active_user),
    db:           AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Return the authenticated user's dashboard statistics."""
    return await dashboard_service.get_dashboard(db, current_user.id)
