"""
Unit tests for app/utils/file_manager.py
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from app.utils.file_manager import (
    cleanup_temp_files,
    delete_file,
    generate_unique_filename,
    get_file_metadata,
    save_file,
)


# ------------------------------------------------------------------ #
# generate_unique_filename
# ------------------------------------------------------------------ #

def test_unique_filename_preserves_pdf_extension() -> None:
    name = generate_unique_filename("report.pdf")
    assert name.endswith(".pdf")


def test_unique_filename_preserves_png_extension() -> None:
    assert generate_unique_filename("scan.PNG").endswith(".png")


def test_unique_filename_is_unique() -> None:
    names = {generate_unique_filename("x.pdf") for _ in range(50)}
    assert len(names) == 50  # All 50 should be distinct


def test_unique_filename_correct_length() -> None:
    # UUID (36) + "." + ext (3) = 40 for .pdf
    assert len(generate_unique_filename("a.pdf")) == 40


# ------------------------------------------------------------------ #
# save_file / delete_file / get_file_metadata
# ------------------------------------------------------------------ #

def test_save_creates_file(tmp_path: Path) -> None:
    content = b"hello test"
    path = save_file(content, str(tmp_path), "test.txt")
    assert path.exists()
    assert path.read_bytes() == content


def test_save_creates_missing_directory(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c"
    save_file(b"data", str(nested), "x.txt")
    assert (nested / "x.txt").exists()


def test_delete_existing_file(tmp_path: Path) -> None:
    p = tmp_path / "del.txt"
    p.write_bytes(b"data")
    assert delete_file(p) is True
    assert not p.exists()


def test_delete_nonexistent_file_returns_false(tmp_path: Path) -> None:
    assert delete_file(tmp_path / "nonexistent.txt") is False


def test_get_file_metadata_returns_correct_info(tmp_path: Path) -> None:
    p = tmp_path / "meta.pdf"
    p.write_bytes(b"%PDF-test")
    meta = get_file_metadata(p)
    assert meta["name"] == "meta.pdf"
    assert meta["size"] == len(b"%PDF-test")
    assert meta["extension"] == ".pdf"
    assert "created_at" in meta


def test_get_file_metadata_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        get_file_metadata(tmp_path / "ghost.txt")


# ------------------------------------------------------------------ #
# cleanup_temp_files
# ------------------------------------------------------------------ #

def test_cleanup_removes_old_files(tmp_path: Path) -> None:
    old_file = tmp_path / "old.txt"
    old_file.write_bytes(b"old")
    # Back-date the modification time by 2 hours
    old_mtime = time.time() - 7200
    import os
    os.utime(old_file, (old_mtime, old_mtime))

    deleted = cleanup_temp_files(str(tmp_path), max_age_hours=1.0)
    assert deleted == 1
    assert not old_file.exists()


def test_cleanup_keeps_recent_files(tmp_path: Path) -> None:
    recent = tmp_path / "recent.txt"
    recent.write_bytes(b"new")
    deleted = cleanup_temp_files(str(tmp_path), max_age_hours=1.0)
    assert deleted == 0
    assert recent.exists()


def test_cleanup_nonexistent_directory_returns_zero() -> None:
    assert cleanup_temp_files("/nonexistent/path/xyz") == 0
