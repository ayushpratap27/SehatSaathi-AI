"""Pydantic schemas for dashboard and report management APIs."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RecentReport(BaseModel):
    id:                str
    original_filename: str
    status:            str
    patient_name:      Optional[str]
    risk_level:        Optional[str]
    created_at:        str

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    total_reports:       int
    reports_this_month:  int
    completed_analyses:  int
    recent_reports:      List[RecentReport] = Field(default_factory=list)


class ReportDetailResponse(BaseModel):
    id:                str
    original_filename: str
    saved_filename:    str
    file_size:         int
    mime_type:         str
    status:            str
    patient_name:      Optional[str]
    report_date:       Optional[str]
    vector_index_path: Optional[str]
    created_at:        str

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: List[ReportDetailResponse]
    total:   int
    limit:   int
    offset:  int


class ChatHistoryItem(BaseModel):
    id:         str
    role:       str
    content:    str
    confidence: Optional[float]
    created_at: str

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id:        str
    title:     str
    messages:  List[ChatHistoryItem] = Field(default_factory=list)
    created_at: str

    model_config = {"from_attributes": True}
