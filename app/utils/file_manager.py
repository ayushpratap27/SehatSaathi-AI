"""
File management utilities — generate names, save, delete, metadata, cleanup.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_unique_filename(original_filename: str) -> str:
    """
    Create a UUID-based filename that preserves the original extension.

    Args:
        original_filename: Filename as provided by the client.

    Returns:
        A collision-safe string like ``"3f2504e0-...-.pdf"``.
    """
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"


def save_file(content: bytes, directory: str, filename: str) -> Path:
    """
    Write ``content`` to ``<directory>/<filename>``.

    Creates ``directory`` (and any parents) if it does not already exist.

    Args:
        content:   Raw bytes to write.
        directory: Target directory path string.
        filename:  Target filename (should be UUID-based to avoid collisions).

    Returns:
        Resolved :class:`pathlib.Path` of the newly created file.
    """
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / filename
    file_path.write_bytes(content)

    logger.debug("Saved %d bytes → %s", len(content), file_path)
    return file_path.resolve()


def delete_file(file_path: "str | Path") -> bool:
    """
    Delete a file from disk.

    Args:
        file_path: Path to the file.

    Returns:
        ``True`` if the file was deleted; ``False`` if it did not exist.
    """
    path = Path(file_path)
    if path.exists():
        path.unlink()
        logger.debug("Deleted: %s", path)
        return True
    logger.warning("delete_file: path not found: %s", path)
    return False


def get_file_metadata(file_path: "str | Path") -> dict:
    """
    Return basic filesystem metadata for a file.

    Args:
        file_path: Path to the target file.

    Returns:
        Dictionary with keys ``name``, ``size``, ``extension``,
        ``created_at``, ``modified_at``.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "extension": path.suffix.lower(),
        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def cleanup_temp_files(directory: str, max_age_hours: float = 24.0) -> int:
    """
    Delete files in ``directory`` that are older than ``max_age_hours``.

    Args:
        directory:     Directory to scan for stale files.
        max_age_hours: Files older than this many hours are removed.

    Returns:
        Number of files deleted.
    """
    target_dir = Path(directory)
    if not target_dir.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    deleted = 0

    for item in target_dir.iterdir():
        if item.is_file() and item.stat().st_mtime < cutoff:
                try:
                    item.unlink()
                    deleted += 1
                    logger.debug("Removed stale temp file: %s", item)
                except OSError as exc:
                    logger.warning("Could not delete stale temp file %s: %s", item, exc)
    if deleted:
        logger.info("Cleaned up %d temp file(s) from '%s'", deleted, directory)

    return deleted
