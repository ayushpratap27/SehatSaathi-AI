"""
OCR engine wrapper around PaddleOCR.

Uses a lazy singleton so the model is loaded only once per process.
Supports scanned PDFs (rendered page-by-page via PyMuPDF) and
direct image files (PNG, JPG, TIFF).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ai.preprocessing.image_preprocessor import (
    bytes_to_array,
    load_image,
    preprocess_for_ocr,
)

logger = logging.getLogger(__name__)


class OCREngine:
    """
    Singleton wrapper around PaddleOCR.

    PaddleOCR downloads its model weights on first initialisation (~200 MB).
    The singleton pattern ensures this happens at most once per process.

    Usage::

        engine = OCREngine.get_instance()
        text   = engine.extract_from_image_path("scan.png")
        result = engine.extract_from_pdf("report.pdf")
    """

    _instance: Optional["OCREngine"] = None
    _ocr: Any = None
    _ready: bool = False

    # ------------------------------------------------------------------ #
    # Singleton constructor
    # ------------------------------------------------------------------ #

    def __new__(cls) -> "OCREngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "OCREngine":
        """Return the ready singleton; initialises on first call."""
        engine = cls()
        if not engine._ready:
            engine._initialize()
        return engine

    # ------------------------------------------------------------------ #
    # Initialisation
    # ------------------------------------------------------------------ #

    def _initialize(self) -> None:
        """
        Load PaddleOCR model weights.

        Raises:
            RuntimeError: If ``paddleocr`` package is not installed.
        """
        try:
            from paddleocr import PaddleOCR  # type: ignore[import]  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed.\n"
                "Install with:  pip install paddlepaddle paddleocr"
            ) from exc

        # Suppress PaddlePaddle's verbose C++ logging
        os.environ.setdefault("GLOG_v", "0")
        os.environ.setdefault("FLAGS_call_stack_level", "0")

        logger.info("Initialising PaddleOCR (first call — may take a moment)…")
        self._ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=False,
            show_log=False,
        )
        self._ready = True
        logger.info("PaddleOCR ready.")

    # ------------------------------------------------------------------ #
    # Core OCR runner
    # ------------------------------------------------------------------ #

    def _run_ocr(self, image: np.ndarray) -> str:
        """
        Run PaddleOCR on a preprocessed NumPy image array.

        Args:
            image: Preprocessed image (grayscale or BGR NumPy array).

        Returns:
            Recognised text lines joined with ``\\n``.
        """
        # PaddleOCR expects a 3-channel image
        if len(image.shape) == 2:
            image = np.stack([image, image, image], axis=-1)

        result = self._ocr.ocr(image, cls=True)

        if not result or result[0] is None:
            return ""

        lines: List[str] = []
        for line in result[0]:
            if line and len(line) >= 2:
                text_info = line[1]
                if text_info and text_info[0]:
                    lines.append(str(text_info[0]))

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Public extraction methods
    # ------------------------------------------------------------------ #

    def extract_from_image_path(self, image_path: "str | Path") -> str:
        """
        Extract text from an image file on disk.

        Applies the full preprocessing pipeline before OCR.

        Args:
            image_path: Path to a PNG, JPG, JPEG, or TIFF image.

        Returns:
            Extracted text string.

        Raises:
            ValueError: If the image file cannot be loaded.
            RuntimeError: If PaddleOCR is not installed.
        """
        logger.info("OCR ← image: %s", Path(image_path).name)
        image = load_image(str(image_path))
        processed = preprocess_for_ocr(image)
        text = self._run_ocr(processed)
        logger.debug("OCR extracted %d chars from image", len(text))
        return text

    def extract_from_image_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from raw image bytes.

        Args:
            image_bytes: Encoded image data (PNG, JPEG, etc.).

        Returns:
            Extracted text string.
        """
        image = bytes_to_array(image_bytes)
        processed = preprocess_for_ocr(image)
        return self._run_ocr(processed)

    def extract_from_pdf(self, pdf_path: "str | Path") -> Dict[str, Any]:
        """
        Extract text from a scanned PDF by rendering each page as an image.

        Each page is rendered at 2× zoom (≈ 144 DPI) for better OCR quality.

        Args:
            pdf_path: Path to the scanned PDF file.

        Returns:
            Dictionary with:
            - ``text``  (str):  All pages joined with double newlines.
            - ``pages`` (int):  Total number of pages processed.

        Raises:
            RuntimeError: If PaddleOCR is not installed or PyMuPDF is unavailable.
        """
        import fitz  # noqa: PLC0415  # PyMuPDF

        pdf_path = Path(pdf_path)
        logger.info("OCR ← scanned PDF: %s", pdf_path.name)

        doc = fitz.open(str(pdf_path))
        page_texts: List[str] = []

        for page_num, page in enumerate(doc):
            # 2× zoom gives ~144 DPI — better OCR accuracy without excessive RAM
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")

            logger.debug("OCR page %d/%d of %s", page_num + 1, len(doc), pdf_path.name)
            page_text = self.extract_from_image_bytes(img_bytes)
            page_texts.append(page_text)

        doc.close()

        full_text = "\n\n".join(page_texts)
        logger.info(
            "OCR finished: %d pages, %d chars from '%s'",
            len(page_texts), len(full_text), pdf_path.name,
        )
        return {"text": full_text, "pages": len(page_texts)}
