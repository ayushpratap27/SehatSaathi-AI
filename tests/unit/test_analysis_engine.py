"""
Unit tests for Phase 4 — Medical Analysis Engine.

Covers: reference engine, status engine, critical detector,
        insight generator, recommendation engine, report analyzer API.
"""

from __future__ import annotations

import pytest

# ------------------------------------------------------------------ #
# Reference Engine
# ------------------------------------------------------------------ #

class TestReferenceEngine:
    def test_resolves_hemoglobin_male(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        cfg, rng, _ = reference_engine.resolve("Hemoglobin", gender="Male", age=30)
        assert cfg is not None
        assert rng is not None
        assert rng.min == 13.5
        assert rng.max == 17.5

    def test_resolves_hemoglobin_female(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        cfg, rng, _ = reference_engine.resolve("Hemoglobin", gender="Female", age=30)
        assert rng is not None
        assert rng.min == 12.0
        assert rng.max == 15.5

    def test_resolves_by_alias(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        cfg, rng, _ = reference_engine.resolve("Hb", gender="Male", age=30)
        assert cfg is not None
        assert cfg.display_name == "Hemoglobin"

    def test_returns_none_for_unknown_test(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        cfg, rng, _ = reference_engine.resolve("UnobtainiumLevel")
        assert cfg is None
        assert rng is None

    def test_resolves_wbc(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        _, rng, crit = reference_engine.resolve("WBC Count")
        assert rng is not None
        assert rng.min == 4000
        assert rng.max == 11000

    def test_resolves_potassium_with_critical(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        _, rng, crit = reference_engine.resolve("Potassium")
        assert rng is not None
        assert crit is not None
        assert crit.low == 2.5
        assert crit.high == 6.5

    def test_known_tests_not_empty(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        assert len(reference_engine.known_tests()) > 0

    def test_contains_operator(self) -> None:
        from ai.analysis.reference_engine import reference_engine
        assert "Hemoglobin" in reference_engine
        assert "xyz_unknown" not in reference_engine


# ------------------------------------------------------------------ #
# Status Engine
# ------------------------------------------------------------------ #

class TestStatusEngine:
    def setup_method(self) -> None:
        from ai.analysis.reference_engine import NumericRange
        from ai.analysis.status_engine import StatusEngine
        self.engine = StatusEngine()
        self.normal_range = NumericRange(min=13.5, max=17.5)

    def test_normal_value(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status(14.5, self.normal_range) == Status.NORMAL

    def test_low_value(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status(12.0, self.normal_range) == Status.LOW

    def test_high_value(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status(19.0, self.normal_range) == Status.HIGH

    def test_very_low_value(self) -> None:
        from ai.analysis.medical_rules import Status
        # 6.0 is < 13.5 * 0.7 → Very Low
        assert self.engine.get_status(6.0, self.normal_range) == Status.VERY_LOW

    def test_very_high_value(self) -> None:
        from ai.analysis.medical_rules import Status
        # 23.0 is > 17.5 * 1.3 → Very High
        assert self.engine.get_status(23.0, self.normal_range) == Status.VERY_HIGH

    def test_critical_low(self) -> None:
        from ai.analysis.medical_rules import Status
        from ai.analysis.reference_engine import CriticalThresholds
        crit = CriticalThresholds(low=7.0)
        result = self.engine.get_status(6.5, self.normal_range, crit)
        assert result == Status.CRITICAL_LOW

    def test_critical_high(self) -> None:
        from ai.analysis.medical_rules import Status
        from ai.analysis.reference_engine import CriticalThresholds
        crit = CriticalThresholds(high=20.0)
        result = self.engine.get_status(21.0, self.normal_range, crit)
        assert result == Status.CRITICAL_HIGH

    def test_none_value_returns_unknown(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status(None, self.normal_range) == Status.UNKNOWN

    def test_no_range_returns_unknown(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status(14.5, None) == Status.UNKNOWN

    def test_qualitative_normal(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status("Negative", None) == Status.NORMAL

    def test_qualitative_positive(self) -> None:
        from ai.analysis.medical_rules import Status
        assert self.engine.get_status("Positive", None) == Status.POSITIVE

    def test_is_abnormal_true(self) -> None:
        assert self.engine.is_abnormal("Low") is True
        assert self.engine.is_abnormal("High") is True
        assert self.engine.is_abnormal("Critical Low") is True

    def test_is_abnormal_false(self) -> None:
        assert self.engine.is_abnormal("Normal") is False


# ------------------------------------------------------------------ #
# Critical Value Detector
# ------------------------------------------------------------------ #

class TestCriticalValueDetector:
    def setup_method(self) -> None:
        from ai.analysis.critical_value_detector import CriticalValueDetector
        self.detector = CriticalValueDetector()

    def test_critical_low_hemoglobin(self) -> None:
        assert self.detector.is_critical("Hemoglobin", 6.5, None) is True

    def test_critical_low_potassium(self) -> None:
        assert self.detector.is_critical("Potassium", 2.2, None) is True

    def test_not_critical_normal_hb(self) -> None:
        assert self.detector.is_critical("Hemoglobin", 14.0, None) is False

    def test_critical_glucose(self) -> None:
        assert self.detector.is_critical("Glucose", 450, None) is True

    def test_critical_platelets(self) -> None:
        assert self.detector.is_critical("Platelet Count", 15000, None) is True


# ------------------------------------------------------------------ #
# Insight Generator
# ------------------------------------------------------------------ #

class TestInsightGenerator:
    def setup_method(self) -> None:
        from ai.analysis.insight_generator import InsightGenerator
        from ai.analysis.reference_engine import NumericRange
        self.gen = InsightGenerator()
        self.rng = NumericRange(min=13.5, max=17.5)

    def test_normal_insight(self) -> None:
        from ai.analysis.medical_rules import Status
        insight = self.gen.generate("Hemoglobin", 14.5, "g/dL", Status.NORMAL, self.rng)
        assert "within the normal" in insight.lower()
        assert "14.5" in insight

    def test_low_insight(self) -> None:
        from ai.analysis.medical_rules import Status
        insight = self.gen.generate("Hemoglobin", 12.4, "g/dL", Status.LOW, self.rng)
        assert "below" in insight.lower()

    def test_critical_low_insight_has_warning(self) -> None:
        from ai.analysis.medical_rules import Status
        insight = self.gen.generate("Potassium", 2.2, "mEq/L", Status.CRITICAL_LOW, None)
        assert "CRITICAL" in insight

    def test_high_insight(self) -> None:
        from ai.analysis.medical_rules import Status
        insight = self.gen.generate("WBC Count", 15000, "/uL", Status.HIGH, self.rng)
        assert "above" in insight.lower()


# ------------------------------------------------------------------ #
# Recommendation Engine
# ------------------------------------------------------------------ #

class TestRecommendationEngine:
    def setup_method(self) -> None:
        from ai.analysis.recommendation_engine import RecommendationEngine
        self.engine = RecommendationEngine()

    def test_always_includes_physician_advice(self) -> None:
        from app.schemas.analysis import AnalysisSummary
        s = AnalysisSummary(total_tests=5, normal=5, abnormal=0,
                             critical=0, high=0, low=0, unknown=0)
        recs = self.engine.generate(s, "Normal")
        assert any("physician" in r.lower() for r in recs)

    def test_critical_recommendation_present(self) -> None:
        from app.schemas.analysis import AnalysisSummary
        s = AnalysisSummary(total_tests=5, normal=4, abnormal=1,
                             critical=1, high=0, low=1, unknown=0)
        recs = self.engine.generate(s, "Critical")
        assert any("critical" in r.lower() or "immediate" in r.lower() for r in recs)

    def test_no_diagnosis_in_recs(self) -> None:
        from app.schemas.analysis import AnalysisSummary
        s = AnalysisSummary(total_tests=5, normal=3, abnormal=2,
                             critical=0, high=1, low=1, unknown=0)
        recs = self.engine.generate(s, "Moderate")
        for r in recs:
            # Should not diagnose diseases or prescribe new medicines
            assert "you have" not in r.lower()
            assert "you are suffering" not in r.lower()
            assert "take this medicine" not in r.lower()


# ------------------------------------------------------------------ #
# Report Analyzer (full pipeline)
# ------------------------------------------------------------------ #

class TestReportAnalyzer:
    SAMPLE_REPORT_DICT = {
        "patient": {"name": "John Doe", "age": 45, "gender": "Male"},
        "tests": [
            {"test_name": "Hemoglobin", "value": 12.4, "unit": "g/dL",
             "reference_range": "13.5-17.5"},
            {"test_name": "WBC Count", "value": 11200, "unit": "/uL",
             "reference_range": "4000-11000"},
            {"test_name": "Glucose", "value": 95, "unit": "mg/dL",
             "reference_range": "70-100"},
            {"test_name": "Potassium", "value": 2.2, "unit": "mEq/L",
             "reference_range": "3.5-5.0"},
        ],
        "diagnosis": ["Iron Deficiency Anemia"],
        "medicines": [],
    }

    def test_full_analysis_returns_result(self, client) -> None:
        r = client.post("/api/v1/analysis/analyze", json=self.SAMPLE_REPORT_DICT)
        assert r.status_code == 200

    def test_analysis_response_shape(self, client) -> None:
        r = client.post("/api/v1/analysis/analyze", json=self.SAMPLE_REPORT_DICT)
        data = r.json()
        assert "analysis" in data
        assert "risk_level" in data
        assert "summary" in data
        assert "recommendations" in data
        assert "disclaimer" in data

    def test_analysis_counts_correct(self, client) -> None:
        r = client.post("/api/v1/analysis/analyze", json=self.SAMPLE_REPORT_DICT)
        analysis = r.json()["analysis"]
        assert analysis["total_tests"] == 4
        assert analysis["normal"] >= 1    # Glucose should be Normal

    def test_critical_potassium_detected(self, client) -> None:
        r = client.post("/api/v1/analysis/analyze", json=self.SAMPLE_REPORT_DICT)
        data = r.json()
        critical = [t for t in data["tests"] if t["test_name"] == "Potassium"]
        assert critical[0]["is_critical"] is True
        assert data["risk_level"] == "Critical"

    def test_disclaimer_always_present(self, client) -> None:
        r = client.post("/api/v1/analysis/analyze", json=self.SAMPLE_REPORT_DICT)
        assert "DISCLAIMER" in r.json()["disclaimer"].upper()

    def test_insights_only_for_abnormal(self, client) -> None:
        r = client.post("/api/v1/analysis/analyze", json=self.SAMPLE_REPORT_DICT)
        data = r.json()
        # Insights should exclude the Normal Glucose
        insights_text = " ".join(data["insights"])
        # Glucose is Normal — no insight about it should appear in the list
        # (it should appear in the tests array but not in insights)
        assert len(data["insights"]) < len(data["tests"])

    def test_empty_tests_returns_result(self, client) -> None:
        empty = {"patient": {}, "tests": [], "diagnosis": [], "medicines": []}
        r = client.post("/api/v1/analysis/analyze", json=empty)
        assert r.status_code == 200
        assert r.json()["analysis"]["total_tests"] == 0
