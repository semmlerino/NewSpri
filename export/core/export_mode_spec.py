"""
Registry contract for export modes.

ExportModeSpec collapses the four parallel if/elif chains that used to live in
``ExportWorker.run``, ``ModernExportSettings._setup_for_preset`` / ``get_data``,
and ``ExportCoordinator.handle_export_request`` into a single per-mode record.

Adding a new export mode now requires only:
  1. A new ``ExportMode`` enum value.
  2. A new ``_SettingsPanelBase`` subclass for its UI.
  3. A new worker method on ``ExportWorker``.
  4. A new entry in ``MODE_SPECS`` (in ``export_presets.py``).

No edits to coordinator or wizard dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QPixmap

    from core.export_coordinator import ExportCoordinator
    from export.core.frame_exporter import ExportConfig, ExportMode, ExportWorker
    from export.dialogs.modern_settings_preview import (
        ModernExportSettings,
        _SettingsPanelBase,
    )

    PanelFactory = Callable[[ModernExportSettings], _SettingsPanelBase]
    DataExtractor = Callable[[ModernExportSettings], dict[str, Any]]
    WorkerMethod = Callable[[ExportWorker], None]
    CoordinatorMethod = Callable[[ExportCoordinator, ExportConfig, "list[QPixmap] | None"], None]


@dataclass(frozen=True)
class ExportModeSpec:
    """Per-mode dispatch record consumed by worker, dialog, and coordinator.

    Callable fields are stored as unbound methods / module-level functions and
    invoked at the call site with an explicit ``self`` argument, e.g.:
        ``spec.worker_method(worker_instance)``
        ``spec.panel_factory(modern_settings_instance).build()``
        ``spec.data_extractor(modern_settings_instance)``
        ``spec.coordinator_method(coordinator_instance, config, frames)``
    """

    mode: ExportMode
    display_name: str
    panel_factory: PanelFactory
    data_extractor: DataExtractor
    worker_method: WorkerMethod
    coordinator_method: CoordinatorMethod
