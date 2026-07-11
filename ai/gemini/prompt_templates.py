"""
Prompt templates for all Gemini AI interactions.

Each template is a pure-Python function that takes structured data
(ParsedReport, ReportAnalysisResult, optional question) and returns
a complete, ready-to-send prompt string.

Design principles:
- All context is embedded in the prompt (no RAG).
- Gemini receives only pre-structured JSON, never raw text or PDFs.
- Every prompt embeds guardrail instructions.
- Every prompt specifies the required output format (JSON).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ai.gemini.medical_guardrails import SYSTEM_INSTRUCTION

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _serialise(obj: Any) -> str:
    """Convert a Pydantic model or dict to a compact, readable JSON string."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(exclude_none=True)
    elif isinstance(obj, dict):
        data = obj
    else:
        data = {}
    return json.dumps(data, indent=2, default=str)


def _report_block(report: Any, analysis: Any) -> str:
    """Build the shared context block used in every prompt."""
    parts = [
        "=== PATIENT REPORT (structured JSON — use ONLY this data) ===",
        _serialise(report),
    ]
    if analysis:
        parts += [
            "",
            "=== CLINICAL ANALYSIS (structured JSON — use ONLY this data) ===",
            _serialise(analysis),
        ]
    return "\n".join(parts)


# ------------------------------------------------------------------ #
# Template 1 — Executive Summary
# ------------------------------------------------------------------ #

def summary_prompt(report: Any, analysis: Any) -> str:
    """
    Build the prompt for generating an executive summary.

    The output must be valid JSON matching the ``SummaryResponse`` schema.
    """
    context = _report_block(report, analysis)
    return f"""{SYSTEM_INSTRUCTION}

{context}

---
TASK: Generate a comprehensive, patient-friendly summary of this medical report.

Return ONLY valid JSON in exactly this structure (no markdown, no extra text):
{{
  "executive_summary": "3-5 sentence overview of the overall report for a medical professional",
  "patient_summary": "3-5 sentence plain-language explanation for the patient (no jargon)",
  "important_findings": ["Key finding 1", "Key finding 2"],
  "abnormal_tests": [
    {{
      "test_name": "Test name from the report",
      "value": "Observed value",
      "unit": "Unit",
      "status": "High/Low/Critical etc.",
      "explanation": "Simple 1-sentence explanation of what this means for the patient"
    }}
  ],
  "medicines": ["Medicine 1", "Medicine 2"],
  "diagnosis": ["Diagnosis 1"],
  "follow_up": [
    "General follow-up suggestion 1 (no specific medical prescriptions)",
    "General follow-up suggestion 2"
  ]
}}

RULES:
- Include ONLY tests, medicines, and diagnoses found in the provided JSON.
- Do NOT add any information not in the report.
- All "abnormal_tests" entries must correspond to tests actually present in the report.
- "follow_up" items must be general (e.g., "Discuss results with your doctor") — never specific prescriptions.
- End your response with a JSON object. No preamble. No markdown code blocks.
"""


# ------------------------------------------------------------------ #
# Template 2 — Medical Explanations
# ------------------------------------------------------------------ #

def explanation_prompt(report: Any, analysis: Any) -> str:
    """
    Build the prompt for generating plain-language medical explanations.

    Covers every abnormal test, every diagnosis, and every medicine
    mentioned in the report.
    """
    context = _report_block(report, analysis)
    return f"""{SYSTEM_INSTRUCTION}

{context}

---
TASK: Generate simple, easy-to-understand explanations for each entity found in this report.

Generate explanations for:
1. Each laboratory test that is abnormal or critical (explain what the test measures and what the result means in simple terms).
2. Each diagnosis mentioned in the report (explain the term in plain language — do NOT add clinical details beyond what is in the report).
3. Each medicine mentioned (explain what it is generally used for — NOT dosage, NOT recommendation to take it).

Return ONLY valid JSON in exactly this structure (no markdown, no extra text):
{{
  "explanations": [
    {{
      "term": "Name of the test, medicine, or diagnosis",
      "category": "lab_test | medicine | diagnosis | medical_term",
      "value": "Observed value with unit (for lab tests), null for others",
      "explanation": "Simple 2-3 sentence explanation suitable for a non-medical reader"
    }}
  ]
}}

RULES:
- Include ONLY items found in the provided report JSON.
- Explanations must be based on the actual values in the report.
- Do NOT explain tests that are not in the report.
- For medicines: explain what they are generally used for, do NOT recommend taking them.
- Keep all explanations under 100 words each.
"""


# ------------------------------------------------------------------ #
# Template 3 — Grounded Chat
# ------------------------------------------------------------------ #

def chat_prompt(question: str, report: Any, analysis: Any) -> str:
    """
    Build the prompt for answering a specific user question about their report.

    The answer must be strictly grounded in the provided data.
    """
    context = _report_block(report, analysis)
    return f"""{SYSTEM_INSTRUCTION}

{context}

---
USER QUESTION: {question}

TASK: Answer the user's question using ONLY the information in the report JSON above.

IMPORTANT:
- If the answer cannot be found in the provided data, respond with exactly:
  "This information is not available in the uploaded report."
- Do NOT use external knowledge to answer the question.
- Keep the answer concise and clear (2-5 sentences unless a longer list is required).
- Do NOT diagnose diseases or recommend medicines.
- End with: "Please consult your healthcare provider for medical advice."
"""


# ------------------------------------------------------------------ #
# Template 4 — Single term explanation (used internally)
# ------------------------------------------------------------------ #

def term_explanation_prompt(term: str, context_json: str) -> str:
    """
    Build a focused prompt to explain one specific medical term.

    Used as a fallback when the main explanation prompt misses a term.
    """
    return f"""{SYSTEM_INSTRUCTION}

REPORT CONTEXT:
{context_json}

---
TASK: Explain the medical term "{term}" in simple, plain language.

The explanation must:
- Be 2-3 sentences maximum.
- Be understandable by someone with no medical background.
- Reference the value from the report if this is a lab test.
- NOT diagnose, prescribe, or provide treatment advice.

Return ONLY the explanation text (no JSON wrapper, no preamble).
"""


# ------------------------------------------------------------------ #
# Template 5 — Strict retry (used when first attempt is rejected)
# ------------------------------------------------------------------ #

def strict_retry_prompt(original_prompt: str, rejection_reason: str) -> str:
    """
    Build a stricter version of a prompt after a validation failure.

    Adds an explicit instruction to correct the specific issue detected.
    """
    return f"""{original_prompt}

IMPORTANT CORRECTION: Your previous response was rejected because: {rejection_reason}

Please regenerate your response, ensuring:
- You use ONLY the data provided in the report JSON above.
- You do NOT include any information not explicitly present in the report.
- Your response is valid JSON matching the requested schema exactly.
"""
