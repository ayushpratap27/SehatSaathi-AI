"""
Report and ReportAnalysis ORM models.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, _new_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chat import ChatSession


class ReportStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"


class Report(Base, TimestampMixin):
    """
    Represents one uploaded medical report document.

    Tracks file metadata, processing status, and links to
    the extracted analysis and chat sessions.
    """

    __tablename__ = "reports"

    id:                Mapped[str]           = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id:           Mapped[str]           = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str]           = mapped_column(String(255), nullable=False)
    saved_filename:    Mapped[str]           = mapped_column(String(255), nullable=False)
    file_path:         Mapped[str]           = mapped_column(String(500), nullable=False)
    file_size:         Mapped[int]           = mapped_column(Integer, nullable=False)
    mime_type:         Mapped[str]           = mapped_column(String(100), nullable=False, default="application/pdf")
    status:            Mapped[str]           = mapped_column(String(20), nullable=False, default=ReportStatus.PENDING.value)
    patient_name:      Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    report_date:       Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vector_index_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_deleted:        Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user:          Mapped["User"]                    = relationship("User",           back_populates="reports")
    analysis:      Mapped[Optional["ReportAnalysis"]] = relationship("ReportAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]]        = relationship("ChatSession",    back_populates="report",  cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Report id={self.id!r} file={self.original_filename!r} status={self.status!r}>"


class ReportAnalysis(Base, TimestampMixin):
    """
    Stores all analysis artefacts for one report.

    Uses Text columns for large JSON blobs to ensure compatibility
    with both SQLite (dev) and PostgreSQL (prod).
    """

    __tablename__ = "report_analyses"

    id:              Mapped[str]           = mapped_column(String(36), primary_key=True, default=_new_uuid)
    report_id:       Mapped[str]           = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    extracted_text:  Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # ParsedReport JSON
    analysis_json:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # ReportAnalysisResult JSON
    summary_json:    Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # SummaryResponse JSON
    risk_level:      Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    total_tests:     Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    abnormal_count:  Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    critical_count:  Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationship
    report: Mapped["Report"] = relationship("Report", back_populates="analysis")
