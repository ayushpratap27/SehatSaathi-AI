"""
Medical NLP pipeline — optional spaCy / SciSpaCy integration.

The pipeline degrades gracefully:
  1. SciSpaCy  ``en_core_sci_md``  (best — biomedical NER + abbreviations)
  2. spaCy     ``en_core_web_sm``  (good  — general English NER)
  3. spaCy blank  ``en``           (minimal — sentence splitting only)
  4. Regex-only fallback            (no spaCy installed)

All extractors query :meth:`MedicalNLP.nlp` to get the pipeline.
If spaCy is unavailable they fall back to pure regex.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class MedicalNLP:
    """
    Lazy singleton wrapping the spaCy / SciSpaCy NLP pipeline.

    Usage::

        pipeline = MedicalNLP.get_instance()
        if pipeline.available:
            doc = pipeline.nlp("Patient has iron deficiency anaemia.")
            for ent in doc.ents:
                print(ent.text, ent.label_)
    """

    _instance: Optional["MedicalNLP"] = None
    _nlp: Any = None
    _model_name: str = "none"
    _initialized: bool = False

    def __new__(cls) -> "MedicalNLP":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MedicalNLP":
        """Return the ready singleton (initialises on first call)."""
        obj = cls()
        if not obj._initialized:
            obj._load()
        return obj

    # ------------------------------------------------------------------ #
    # Initialisation
    # ------------------------------------------------------------------ #

    def _load(self) -> None:
        """Try to load the best available NLP model."""
        self._initialized = True

        # --- Attempt 1: SciSpaCy en_core_sci_md ---
        if self._try_scispacy():
            return

        # --- Attempt 2: spaCy en_core_web_sm ---
        if self._try_spacy("en_core_web_sm"):
            return

        # --- Attempt 3: Blank spaCy (sentence detection only) ---
        if self._try_blank_spacy():
            return

        # --- Fallback: no spaCy ---
        logger.warning(
            "spaCy is not installed. Medical extraction will run in regex-only mode. "
            "Install with: pip install spacy && python -m spacy download en_core_web_sm"
        )

    def _try_scispacy(self) -> bool:
        try:
            import spacy  # noqa: PLC0415
            from scispacy.abbreviation import AbbreviationDetector  # noqa: PLC0415

            nlp = spacy.load("en_core_sci_md")
            if "abbreviation_detector" not in nlp.pipe_names:
                nlp.add_pipe("abbreviation_detector")
            self._nlp = nlp
            self._model_name = "scispacy/en_core_sci_md"
            logger.info("NLP pipeline: SciSpaCy (en_core_sci_md)")
            return True
        except Exception as exc:
            logger.debug("SciSpaCy not available: %s", exc)
            return False

    def _try_spacy(self, model: str) -> bool:
        try:
            import spacy  # noqa: PLC0415
            self._nlp = spacy.load(model)
            self._model_name = f"spacy/{model}"
            logger.info("NLP pipeline: spaCy (%s)", model)
            return True
        except Exception as exc:
            logger.debug("spaCy model '%s' not available: %s", model, exc)
            return False

    def _try_blank_spacy(self) -> bool:
        try:
            import spacy  # noqa: PLC0415
            self._nlp = spacy.blank("en")
            # Add sentence detection for basic sentence splitting
            if "sentencizer" not in self._nlp.pipe_names:
                self._nlp.add_pipe("sentencizer")
            self._model_name = "spacy/blank-en"
            logger.info("NLP pipeline: spaCy blank (minimal)")
            return True
        except Exception as exc:
            logger.debug("spaCy blank load failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @property
    def available(self) -> bool:
        """True if any spaCy model was successfully loaded."""
        return self._nlp is not None

    @property
    def model_name(self) -> str:
        """Name of the loaded model, or 'none'."""
        return self._model_name

    def __call__(self, text: str) -> Any:
        """
        Process text through the NLP pipeline.

        Args:
            text: Input text.

        Returns:
            spaCy ``Doc`` object, or ``None`` if spaCy is unavailable.
        """
        if self._nlp is None:
            return None
        return self._nlp(text)

    @property
    def nlp(self) -> Any:
        """The underlying spaCy Language object (may be None)."""
        return self._nlp

    def get_entities(self, text: str) -> List[dict]:
        """
        Extract named entities from text.

        Args:
            text: Input text.

        Returns:
            List of dicts with ``text``, ``label``, ``start``, ``end`` keys.
            Empty list if spaCy is unavailable.
        """
        if not self.available:
            return []
        doc = self._nlp(text)
        return [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]

    def get_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using the NLP pipeline.

        Args:
            text: Input text.

        Returns:
            List of sentence strings.
        """
        if not self.available:
            # Simple fallback: split on sentence-ending punctuation
            import re  # noqa: PLC0415
            return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        doc = self._nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


# Module-level singleton
medical_nlp = MedicalNLP.get_instance()
