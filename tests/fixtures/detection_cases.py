"""
Detection regression baselines for real sprite-sheet fixtures.

These golden values pin the comprehensive auto-detection pipeline against the
PNG fixtures already in ``spritetests/``. If detection heuristics or
``Config.Detection`` thresholds drift, the regression tests in
``tests/unit/test_detection_algorithms.py`` will fail with a clear diff.

The expected values were captured from the working pipeline on 2026-04-28.
When tuning detection on purpose, run the comprehensive_auto_detect probe
to capture new baselines and update this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPRITES_ROOT = PROJECT_ROOT / "spritetests"


@dataclass(frozen=True)
class DetectionBaseline:
    """Golden expectations for a single sprite-sheet fixture."""

    name: str
    relative_path: str
    sheet_width: int
    sheet_height: int
    expected_success: bool
    expected_frame_width: int
    expected_frame_height: int
    expected_offset_x: int
    expected_offset_y: int
    expected_spacing_x: int
    expected_spacing_y: int
    expected_confidence_bucket: str  # "high" | "medium" | "low" | "failed"

    @property
    def absolute_path(self) -> Path:
        return PROJECT_ROOT / self.relative_path


# Captured 2026-04-28 — see comprehensive_auto_detect output.
DETECTION_BASELINES: tuple[DetectionBaseline, ...] = (
    DetectionBaseline(
        name="archer_idle",
        relative_path="spritetests/Archer/Archer_Idle.png",
        sheet_width=1152,
        sheet_height=192,
        expected_success=True,
        expected_frame_width=16,
        expected_frame_height=16,
        expected_offset_x=5,
        expected_offset_y=5,
        expected_spacing_x=0,
        expected_spacing_y=0,
        expected_confidence_bucket="low",
    ),
    DetectionBaseline(
        name="archer_run",
        relative_path="spritetests/Archer_Run.png",
        sheet_width=768,
        sheet_height=192,
        expected_success=True,
        expected_frame_width=16,
        expected_frame_height=16,
        expected_offset_x=5,
        expected_offset_y=5,
        expected_spacing_x=0,
        expected_spacing_y=0,
        expected_confidence_bucket="low",
    ),
    DetectionBaseline(
        name="lancer_idle",
        relative_path="spritetests/Lancer_Idle.png",
        sheet_width=3840,
        sheet_height=320,
        expected_success=True,
        expected_frame_width=16,
        expected_frame_height=16,
        expected_offset_x=5,
        expected_offset_y=5,
        expected_spacing_x=0,
        expected_spacing_y=0,
        expected_confidence_bucket="low",
    ),
    DetectionBaseline(
        name="test_rect_32x48",
        relative_path="spritetests/test_rect_32x48.png",
        sheet_width=138,
        sheet_height=154,
        expected_success=False,
        expected_frame_width=0,
        expected_frame_height=0,
        expected_offset_x=5,
        expected_offset_y=5,
        expected_spacing_x=0,
        expected_spacing_y=0,
        expected_confidence_bucket="low",
    ),
)


__all__ = ["DETECTION_BASELINES", "PROJECT_ROOT", "SPRITES_ROOT", "DetectionBaseline"]
