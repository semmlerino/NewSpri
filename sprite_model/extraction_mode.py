#!/usr/bin/env python3
"""
Extraction Mode Enum
=====================

Defines extraction modes for sprite frame detection.
"""

from enum import Enum


class ExtractionMode(Enum):
    """Extraction mode for sprite frame detection."""

    GRID = "grid"
    CCL = "ccl"
