"""
Report Analyzer — orchestrates the full Phase 4 clinical analysis pipeline.

Pipeline:
    ParsedReport (Phase 3 output)
        ↓
    ReferenceEngine  — resolve ranges per-test (gender/age aware)
        ↓
    StatusEngine     — determine Normal/Low/High/Critical per test
        ↓
    CriticalValueDetector — flag life-threatening values
        ↓
    InsightGenerator — generate plain-language per-test explanation
        ↓
    AbnormalityDetector — aggregate counts
        ↓
    RiskAnalyzer     — overall risk level + summary sentence
        ↓
    RecommendationEngine — general safe recommendations
        ↓
    ReportAnalysisResult (final JSON)
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Union

from ai.analysis.abnormality_detector import abnormality_detector
from ai.analysis.critical_value_detector import critical_value_detector
from ai.analysis.insight_generator import insight_generator
from ai.analysis.medical_rules import Status
from ai.analysis.recommendation_engine import recommendation_engine
from ai.analysis.reference_engine import ReferenceEngine, reference_engine
from ai.analysis.risk_analyzer import risk_analyzer
from ai.analysis.status_engine import status_engine
from app.schemas.analysis import DISCLAIMER, ReportAnalysisResult, TestAnalysisResult
from app.schemas.report import ParsedReport

logger = logging.getLogger(__name__)


class ReportAnalyzer:
    """
    Entry point for the Phase 4 Medical Analysis Engine.

    All sub-engines are injected via constructor arguments, making the
    analyzer easily testable with mock components.
    """

    def __init__(
        self,
        ref_engine: Optional[ReferenceEngine] = None,
    ) -> None:
        self._ref = ref_engine or reference_engine

    def analyze(self, report: ParsedReport) -> ReportAnalysisResult:
        """
        Run the complete analysis pipeline on a parsed medical report.

        Args:
            report: :class:`~app.schemas.report.ParsedReport` from Phase 3.

        Returns:
            :class:`~app.schemas.analysis.ReportAnalysisResult` with full analysis.
        """
        t0 = time.perf_counter()
        logger.info(
            "Analysing report: patient=%s tests=%d",
            report.patient.name or "Unknown",
            len(report.tests),
        )

        gender: Optional[str] = report.patient.gender
        age:    Optional[int] = report.patient.age

        # --- Analyse each test ---
        test_results: List[TestAnalysisResult] = []
        test_dicts:   List[dict] = []

        for lab_test in report.tests:
            result = self._analyse_one_test(lab_test, gender, age)
            test_results.append(result)
            test_dicts.append(result.model_dump())

        # --- Aggregate ---
        summary          = abnormality_detector.summarise(test_dicts)
        abnormal_names   = abnormality_detector.get_abnormal_findings(test_dicts)
        critical_names   = abnormality_detector.get_critical_findings(test_dicts)
        risk_level       = risk_analyzer.get_risk_level(summary)
        report_summary   = risk_analyzer.generate_summary(summary, risk_level)
        recs             = recommendation_engine.generate(
            summary, risk_level, has_medicines=bool(report.medicines)
        )

        # Insights — only for abnormal/critical tests (normal tests are verbose)
        insights = [
            t.insight for t in test_results
            if t.is_abnormal or t.is_critical
        ]

        elapsed = time.perf_counter() - t0
        logger.info(
            "Analysis complete in %.2fs: risk=%s abnormal=%d critical=%d",
            elapsed, risk_level, summary.abnormal, summary.critical,
        )

        return ReportAnalysisResult(
            patient=report.patient.model_dump(exclude_none=True),
            tests=test_results,
            analysis=summary,
            abnormal_findings=abnormal_names,
            critical_findings=critical_names,
            insights=insights,
            risk_level=risk_level,
            summary=report_summary,
            recommendations=recs,
            disclaimer=DISCLAIMER,
        )

    # ---------------------------------------------------------------- #
    # Per-test analysis
    # ---------------------------------------------------------------- #

    def _analyse_one_test(
        self,
        lab_test,
        gender: Optional[str],
        age: Optional[int],
    ) -> TestAnalysisResult:
        """Analyse a single :class:`~app.schemas.report.LabTest`."""

        test_name   = lab_test.test_name
        value       = lab_test.value
        unit        = lab_test.unit
        source_ref  = lab_test.reference_range

        # --- Resolve reference range from knowledge base ---
        cfg, rng, crit = self._ref.resolve(test_name, gender, age)

        # Resolved range string for display
        resolved_ref = rng.as_string() if rng else None
        display_unit = unit or (cfg.unit if cfg else None)

        # --- Determine status ---
        st = status_engine.get_status(value, rng, crit)

        # If status engine says Unknown but we have a source reference range
        # from the report itself, fall back to Phase 3's embedded status
        if st == Status.UNKNOWN and lab_test.status and lab_test.status != "Unknown":
            st = lab_test.status

        is_abn  = status_engine.is_abnormal(st)
        is_crit = (
            status_engine.is_critical(st)
            or critical_value_detector.is_critical(test_name, value, crit)
        )

        # Upgrade status to Critical when safety-net fires
        if is_crit and st not in (Status.CRITICAL_LOW, Status.CRITICAL_HIGH):
            try:
                fval = float(value)  # type: ignore[arg-type]
                if rng and rng.min is not None and fval < rng.min:
                    st = Status.CRITICAL_LOW
                elif rng and rng.max is not None and fval > rng.max:
                    st = Status.CRITICAL_HIGH
                else:
                    st = Status.CRITICAL_HIGH  # conservative default
            except (TypeError, ValueError):
                pass

        # --- Generate insight ---
        insight = insight_generator.generate(
            test_name=test_name,
            value=value,
            unit=display_unit,
            status=st,
            ref_range=rng,
            test_config=cfg,
        )

        return TestAnalysisResult(
            test_name=test_name,
            value=value,
            unit=display_unit,
            reference_range=resolved_ref or source_ref,
            source_reference=source_ref,
            status=st,
            is_abnormal=is_abn,
            is_critical=is_crit,
            insight=insight,
        )


# Module-level singleton
report_analyzer = ReportAnalyzer()
