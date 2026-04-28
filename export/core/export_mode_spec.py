"""Core export-mode dispatch contract.

This module intentionally contains no dialog or widget types. UI-specific mode
configuration lives under ``export.dialogs`` so the export engine can evolve
without importing Qt dialog internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from PySide6.QtGui import QPixmap

    from core.export_coordinator import ExportCoordinator
    from export.core.frame_exporter import ExportConfig, ExportMode, _ExportWorker

    _WorkerMethod = Callable[[_ExportWorker], None]
    _CoordinatorMethod = Callable[
        [ExportCoordinator, ExportConfig, Sequence[QPixmap] | None], None
    ]

__all__: list[str] = []

@dataclass(frozen=True)
class _ExportModeSpec:
    """Per-mode dispatch record consumed by worker and coordinator.

    Callable fields are stored as unbound methods / module-level functions and
    invoked at the call site with an explicit ``self`` argument, e.g.:
        ``spec.worker_method(worker_instance)``
        ``spec.coordinator_method(coordinator_instance, config, frames)``
    """

    mode: ExportMode
    display_name: str
    worker_method: _WorkerMethod
    coordinator_method: _CoordinatorMethod
