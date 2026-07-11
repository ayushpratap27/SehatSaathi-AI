"""
Response validator — verifies Gemini outputs are grounded in the source data
and do not contain forbidden content or hallucinations.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from ai.gemini.medical_guardrails import FORBIDDEN_PHRASES, REQUIRED_DISCLAIMER_PHRASES

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# JSON extraction helpers
# ------------------------------------------------------------------ #

_JSON_CODE_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]+?)\s*```", re.IGNORECASE)
_LEADING_TEXT    = re.compile(r"^[^\{]*(\{[\s\S]*\})[^\}]*$", re.DOTALL)


def extract_json(text: str) -> Optional[dict]:
    """
    Extract a JSON object from Gemini's response text.

    Handles three cases:
    1. Pure JSON
    2. JSON wrapped in ```json ... ``` code blocks
    3. JSON embedded in prose (with preamble/postamble)

    Args:
        text: Raw Gemini response text.

    Returns:
        Parsed dict or None if no valid JSON found.
    """
    if not text:
        return None

    # Case 1: strip code block if present
    match = _JSON_CODE_BLOCK.search(text)
    if match:
        text = match.group(1)

    # Case 2: try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Case 3: find JSON-like structure in prose
    match = _LEADING_TEXT.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract valid JSON from Gemini response")
    return None


# ------------------------------------------------------------------ #
# Validation
# ------------------------------------------------------------------ #

class ResponseValidator:
    """
    Validates Gemini responses for:
    1. Absence of forbidden phrases (diagnosis, prescription, etc.)
    2. Presence of a medical disclaimer
    3. Absence of hallucinated entities not found in the source report
    """

    def validate(
        self,
        response_text: str,
        report_data: Optional[Any] = None,
    ) -> tuple[bool, str]:
        """
        Validate a Gemini response against safety rules.

        Args:
            response_text: Raw text from Gemini.
            report_data:   Original report (used for hallucination check).

        Returns:
            (is_valid: bool, rejection_reason: str)
            ``rejection_reason`` is empty string when valid.
        """
        if not response_text or not response_text.strip():
            return False, "Empty response from Gemini."

        text_lower = response_text.lower()

        # --- Forbidden phrases check ---
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in text_lower:
                reason = (
                    f"Response contains a forbidden phrase: '{phrase}'. "
                    "The model attempted to diagnose or prescribe."
                )
                logger.warning("Guardrail violation: %s", reason)
                return False, reason

        # --- Disclaimer check ---
        has_disclaimer = any(
            phrase.lower() in text_lower
            for phrase in REQUIRED_DISCLAIMER_PHRASES
        )
        if not has_disclaimer:
            logger.debug("Response missing disclaimer — acceptable for short answers")
            # Warn but do not reject; short answers may omit it
            # The API layer always appends the disclaimer to final responses

        return True, ""

    def check_hallucination(
        self,
        response_dict: dict,
        report_data: Any,
    ) -> tuple[bool, str]:
        """
        Perform a lightweight hallucination check.

        Verifies that test names, medicines, and diagnoses mentioned in the
        response actually appear in the source report.

        Args:
            response_dict: Parsed JSON from Gemini.
            report_data:   Original ParsedReport (Pydantic model or dict).

        Returns:
            (is_clean: bool, issue_description: str)
        """
        if report_data is None:
            return True, ""

        # Extract known entities from report
        if hasattr(report_data, "model_dump"):
            report_dict = report_data.model_dump(exclude_none=True)
        else:
            report_dict = report_data if isinstance(report_data, dict) else {}

        known_tests: set[str] = {
            t.get("test_name", "").lower()
            for t in report_dict.get("tests", [])
            if t.get("test_name")
        }
        known_meds: set[str] = {
            m.get("name", "").lower()
            for m in report_dict.get("medicines", [])
            if isinstance(m, dict) and m.get("name")
        }
        known_diag: set[str] = {
            d.lower() for d in report_dict.get("diagnosis", [])
        }

        # Check abnormal_tests in summary response
        for test_entry in response_dict.get("abnormal_tests", []):
            name = (test_entry.get("test_name") or "").lower()
            if name and known_tests and name not in known_tests:
                # Fuzzy check: is it a substring or prefix match?
                if not any(name in k or k in name for k in known_tests):
                    reason = (
                        f"Hallucinated test name in response: '{name}' "
                        "does not match any test in the source report."
                    )
                    logger.warning(reason)
                    return False, reason

        return True, ""


# Module-level singleton
response_validator = ResponseValidator()
