"""
Image preprocessing pipeline for improving OCR accuracy on scanned documents.

All functions operate on NumPy arrays (OpenCV format).
The public ``preprocess_for_ocr`` function applies the full pipeline in order.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Individual preprocessing steps
# ------------------------------------------------------------------ #

def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR image to grayscale. Returns unchanged if already 2-D."""
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def resize_for_ocr(image: np.ndarray, min_side: int = 1000) -> np.ndarray:
    """
    Upscale images whose smallest dimension is below ``min_side`` pixels.

    Low-resolution scans (< 1000 px on the short side) produce poor OCR results.
    Upscaling with cubic interpolation significantly improves character recognition.

    Args:
        image:    Input image.
        min_side: Minimum acceptable dimension in pixels (default: 1000).

    Returns:
        Resized image, or the original if already large enough.
    """
    h, w = image.shape[:2]
    if min(h, w) < min_side:
        scale = min_side / min(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        logger.debug("Resized %dx%d → %dx%d", w, h, new_w, new_h)
    return image


def deskew(image: np.ndarray) -> np.ndarray:
    """
    Correct rotational skew using the minimum-area-rectangle method.

    Skips correction when the estimated angle is less than 0.5° to avoid
    unnecessary resampling of already-straight images.

    Args:
        image: Grayscale or binary image.

    Returns:
        Deskewed image (same dtype and shape).
    """
    gray = to_grayscale(image)

    # White text on dark background works best for contour detection
    if np.mean(gray) > 127:
        gray_inv = cv2.bitwise_not(gray)
    else:
        gray_inv = gray

    coords = np.column_stack(np.where(gray_inv > 0))
    if len(coords) < 5:
        return image  # Too little content to estimate angle

    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    if abs(angle) < 0.5:
        return image  # Already straight enough

    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    logger.debug("Deskewed by %.2f°", angle)
    return rotated


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation).

    Effective for scanned documents with uneven illumination or faded ink.
    """
    gray = to_grayscale(image)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def remove_noise(image: np.ndarray) -> np.ndarray:
    """
    Reduce salt-and-pepper noise with a 3×3 median blur.

    Operates on grayscale; converts if the input is BGR.
    """
    gray = to_grayscale(image)
    return cv2.medianBlur(gray, 3)


def apply_threshold(image: np.ndarray) -> np.ndarray:
    """
    Binarise a grayscale image using Otsu's method.

    Produces a high-contrast black-and-white image suitable for OCR.
    """
    gray = to_grayscale(image)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


# ------------------------------------------------------------------ #
# Full pipeline
# ------------------------------------------------------------------ #

def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Apply the complete preprocessing pipeline for maximum OCR accuracy.

    Steps (in order):
    1. Resize to minimum OCR-friendly resolution
    2. Deskew
    3. Enhance contrast (CLAHE)
    4. Remove noise (median blur)
    5. Binarise (Otsu threshold)

    Args:
        image: Input image as a NumPy array (BGR or grayscale).

    Returns:
        Preprocessed binary image (grayscale uint8).
    """
    image = resize_for_ocr(image)
    image = deskew(image)
    image = enhance_contrast(image)
    image = remove_noise(image)
    image = apply_threshold(image)
    return image


# ------------------------------------------------------------------ #
# I/O helpers
# ------------------------------------------------------------------ #

def load_image(image_path: "str") -> np.ndarray:
    """
    Load an image from disk as a BGR NumPy array.

    Args:
        image_path: Filesystem path to the image file.

    Returns:
        NumPy array in BGR uint8 format.

    Raises:
        ValueError: If OpenCV cannot decode the file.
    """
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")
    return image


def bytes_to_array(image_bytes: bytes) -> np.ndarray:
    """
    Decode raw image bytes into a BGR NumPy array.

    Args:
        image_bytes: Encoded image data (PNG, JPEG, TIFF, …).

    Returns:
        NumPy array in BGR uint8 format.

    Raises:
        ValueError: If OpenCV cannot decode the bytes.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image from bytes.")
    return image
