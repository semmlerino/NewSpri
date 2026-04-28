#!/usr/bin/env python3
"""
Extraction Mode Enum
=====================

Defines extraction modes for sprite frame detection.
"""

from enum import Enum

__all__ = ["ExtractionMode", "extraction_mode_label"]


class ExtractionMode(Enum):
    """Extraction mode for sprite frame detection."""

    GRID = "grid"
    CCL = "ccl"


def extraction_mode_label(mode: ExtractionMode) -> str:
    """Return a user-facing label for an extraction mode."""
    return "CCL" if mode is ExtractionMode.CCL else "Grid"
