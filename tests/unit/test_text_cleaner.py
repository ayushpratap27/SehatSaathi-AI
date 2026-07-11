"""
Unit tests for app/utils/text_cleaner.py
"""

from __future__ import annotations

from app.utils.text_cleaner import clean_text


def test_empty_string_returns_empty() -> None:
    assert clean_text("") == ""


def test_none_like_returns_empty() -> None:
    # Passing an empty string is the closest valid equivalent
    assert clean_text("   ") == ""


def test_multiple_spaces_collapsed() -> None:
    assert clean_text("Hello    World") == "Hello World"


def test_tabs_collapsed() -> None:
    assert clean_text("A\t\t\tB") == "A B"


def test_hyphenated_line_break_merged() -> None:
    assert clean_text("hemo-\nglobin") == "hemoglobin"


def test_single_newline_becomes_space() -> None:
    result = clean_text("Line one\nLine two")
    assert result == "Line one Line two"


def test_paragraph_break_preserved() -> None:
    result = clean_text("Para one.\n\nPara two.")
    assert "Para one." in result and "Para two." in result
    assert "\n\n" in result


def test_excess_newlines_normalised() -> None:
    result = clean_text("A\n\n\n\n\nB")
    assert "\n\n\n" not in result


def test_unit_slash_normalised() -> None:
    assert "g/dL" in clean_text("14.5 g / dL")


def test_unicode_normalised() -> None:
    # NFKC: fi ligature → fi
    result = clean_text("\ufb01le")
    assert result == "file"


def test_ocr_artifact_underscores_removed() -> None:
    result = clean_text("Name: _______  Age: 30")
    assert "___" not in result


def test_strips_leading_trailing_whitespace() -> None:
    assert clean_text("  hello  ") == "hello"


def test_realistic_ocr_output() -> None:
    raw = (
        "Patient  Name:  John  Doe\n"
        "Hemo-\nglobin:  14.5  g / dL\n"
        "Glucose:  95  mg / dL"
    )
    result = clean_text(raw)
    assert "Hemoglobin" in result
    assert "g/dL" in result
    assert "mg/dL" in result
    assert "  " not in result  # no double spaces
