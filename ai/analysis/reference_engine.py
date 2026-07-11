"""
Reference Range Engine — loads YAML configs and resolves test-specific
reference ranges based on patient demographics.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "reference_ranges"


# ------------------------------------------------------------------ #
# Data classes for resolved range data
# ------------------------------------------------------------------ #

@dataclass
class NumericRange:
    """A numeric reference range with optional gender/age filters."""
    min: Optional[float] = None
    max: Optional[float] = None
    gender: Optional[str] = None      # "male" | "female" | None
    age_min: Optional[int] = None
    age_max: Optional[int] = None

    def as_string(self) -> str:
        if self.min is not None and self.max is not None:
            return f"{self.min}-{self.max}"
        if self.max is not None:
            return f"< {self.max}"
        if self.min is not None:
            return f"> {self.min}"
        return ""


@dataclass
class CriticalThresholds:
    """Critical value thresholds for a test."""
    low:  Optional[float] = None
    high: Optional[float] = None


@dataclass
class TestConfig:
    """Full configuration for a single test loaded from YAML."""
    key:          str
    display_name: str
    aliases:      List[str]
    unit:         str
    category:     str
    description:  str
    ranges:       Dict[str, NumericRange] = field(default_factory=dict)
    critical:     Optional[CriticalThresholds] = None


# ------------------------------------------------------------------ #
# Main engine
# ------------------------------------------------------------------ #

class ReferenceEngine:
    """
    Loads reference range YAML files from a directory and provides
    a `resolve()` method that returns the most specific range for a
    given test name and patient demographics.

    The engine is config-driven: add a new YAML file or extend an
    existing one to support new tests — no Python changes required.
    """

    def __init__(self, config_dir: "str | Path" = _DEFAULT_CONFIG_DIR) -> None:
        self._config_dir = Path(config_dir)
        self._tests:     Dict[str, TestConfig] = {}  # key → TestConfig
        self._alias_map: Dict[str, str] = {}         # alias_lower → key
        self._load_all()

    # ---------------------------------------------------------------- #
    # Loading
    # ---------------------------------------------------------------- #

    def _load_all(self) -> None:
        """Load every .yaml / .yml file in the config directory."""
        try:
            import yaml  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "PyYAML is required for the reference engine. "
                "Install with: pip install pyyaml"
            ) from exc

        if not self._config_dir.exists():
            logger.warning(
                "Reference range config directory not found: %s", self._config_dir
            )
            return

        loaded = 0
        for yaml_file in sorted(self._config_dir.glob("*.yaml")):
            try:
                with yaml_file.open("r", encoding="utf-8") as fh:
                    data: Dict[str, Any] = yaml.safe_load(fh) or {}
                for key, cfg in data.items():
                    self._register(key, cfg)
                    loaded += 1
            except Exception as exc:
                logger.error("Failed to load %s: %s", yaml_file.name, exc)

        logger.info(
            "ReferenceEngine: loaded %d tests from %s",
            loaded, self._config_dir,
        )

    def _register(self, key: str, raw: Dict[str, Any]) -> None:
        """Parse a single YAML test entry and register it."""
        aliases: List[str] = [a.lower() for a in raw.get("aliases", [])]
        ranges_raw = raw.get("ranges", {})
        ranges: Dict[str, NumericRange] = {}

        for rname, rdata in ranges_raw.items():
            ranges[rname] = NumericRange(
                min=rdata.get("min"),
                max=rdata.get("max"),
                gender=rdata.get("gender"),
                age_min=rdata.get("age_min"),
                age_max=rdata.get("age_max"),
            )

        crit_raw = raw.get("critical", {})
        critical = (
            CriticalThresholds(
                low=crit_raw.get("low"),
                high=crit_raw.get("high"),
            )
            if crit_raw
            else None
        )

        cfg = TestConfig(
            key=key,
            display_name=raw.get("display_name", key.replace("_", " ").title()),
            aliases=aliases,
            unit=raw.get("unit", ""),
            category=raw.get("category", "Other"),
            description=raw.get("description", ""),
            ranges=ranges,
            critical=critical,
        )

        self._tests[key] = cfg
        # Index by display name and all aliases
        self._alias_map[cfg.display_name.lower()] = key
        self._alias_map[key.lower()] = key
        for alias in aliases:
            self._alias_map[alias] = key

    # ---------------------------------------------------------------- #
    # Resolution
    # ---------------------------------------------------------------- #

    def _find_key(self, test_name: str) -> Optional[str]:
        """Return the canonical key for a test name, or None."""
        normalized = test_name.lower().strip()
        if normalized in self._alias_map:
            return self._alias_map[normalized]
        # Strip punctuation and retry
        clean = re.sub(r"[^a-z0-9\s]", "", normalized).strip()
        if clean in self._alias_map:
            return self._alias_map[clean]
        # Fuzzy match with rapidfuzz (if available)
        try:
            from rapidfuzz import process, fuzz  # noqa: PLC0415
            result = process.extractOne(
                normalized,
                self._alias_map.keys(),
                scorer=fuzz.ratio,
                score_cutoff=85,
            )
            if result:
                return self._alias_map[result[0]]
        except ImportError:
            pass
        return None

    def resolve(
        self,
        test_name: str,
        gender: Optional[str] = None,
        age: Optional[int] = None,
    ) -> Tuple[Optional[TestConfig], Optional[NumericRange], Optional[CriticalThresholds]]:
        """
        Return the most specific reference range for a test.

        Resolution priority:
        1. Gender + age specific range
        2. Gender specific range (any age)
        3. Age specific range (any gender)
        4. "default" range
        5. First available range

        Args:
            test_name: Test name (any alias or normalised form).
            gender:    Patient gender ("Male" | "Female" | None).
            age:       Patient age in years (None if unknown).

        Returns:
            (TestConfig, NumericRange, CriticalThresholds) — any may be None
            if the test is not in the knowledge base.
        """
        key = self._find_key(test_name)
        if not key:
            logger.debug("ReferenceEngine: no config for '%s'", test_name)
            return None, None, None

        cfg = self._tests[key]
        gender_lc = gender.lower() if gender else None

        best: Optional[NumericRange] = None
        best_score: int = -1

        for rng in cfg.ranges.values():
            score = 0

            # Gender match
            if rng.gender:
                if gender_lc and rng.gender.lower() == gender_lc:
                    score += 4
                elif gender_lc:
                    continue   # gender required but doesn't match → skip
                # no gender provided and range requires one → skip
                elif gender_lc is None:
                    continue

            # Age bounds
            if rng.age_min is not None:
                if age is None or age < rng.age_min:
                    continue
                score += 1
            if rng.age_max is not None:
                if age is None or age > rng.age_max:
                    continue
                score += 1

            if score > best_score:
                best_score = score
                best = rng

        # Fallback: default range
        if best is None:
            best = cfg.ranges.get("default")

        # Final fallback: first available range
        if best is None and cfg.ranges:
            best = next(iter(cfg.ranges.values()))

        return cfg, best, cfg.critical

    # ---------------------------------------------------------------- #
    # Convenience
    # ---------------------------------------------------------------- #

    def known_tests(self) -> List[str]:
        """Return all registered display names."""
        return [cfg.display_name for cfg in self._tests.values()]

    def __contains__(self, test_name: str) -> bool:
        return self._find_key(test_name) is not None


# Module-level singleton
reference_engine = ReferenceEngine()
