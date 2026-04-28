"""Data collection and summary formatting for export settings widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt

from export.core.frame_exporter import BackgroundMode, ExportMode, LayoutMode

if TYPE_CHECKING:
    from export.core.export_presets import ExportPreset
    from export.dialogs.modern_settings_preview import _ModernExportSettings


__all__: list[str] = []


# Ordered layout modes. Index matches the QButtonGroup id used by the sheet
# settings panel and by persisted wizard data.
_LAYOUT_MODES: tuple[LayoutMode, ...] = (
    LayoutMode.AUTO,
    LayoutMode.COLUMNS,
    LayoutMode.ROWS,
    LayoutMode.SQUARE,
)

_NAMING_PATTERNS: tuple[str, ...] = (
    "{name}_{index:03d}",
    "{name}-{index}",
    "{name}{index}",
)


class _ExportSettingsDataCollector:
    """Serialize current export settings widget state into wizard data."""

    def __init__(self, parent: _ModernExportSettings) -> None:
        self._parent = parent

    def base_data(self) -> dict[str, Any]:
        """Collect settings shared by every export mode."""
        parent = self._parent
        return {
            "output_dir": parent.path_edit.text(),
            "format": parent.format_combo.currentText(),
            "scale": (parent.scale_group.checkedId() if parent.scale_group.checkedButton() else 1),
        }

    def sheet_data(self) -> dict[str, Any]:
        """Collect sprite sheet export settings."""
        parent = self._parent
        widget = parent._settings_widgets.get("sheet_filename")
        data: dict[str, Any] = {
            "single_filename": widget.text() if widget is not None else "",
            "layout_mode": self.layout_mode(),
            "columns": parent.cols_spin.value(),
            "rows": parent.rows_spin.value(),
        }

        spacing_widget = parent._settings_widgets.get("spacing")
        data["spacing"] = spacing_widget.value() if spacing_widget is not None else 0

        bg_widget = parent._settings_widgets.get("background")
        bg_data = bg_widget.currentData() if bg_widget is not None else None
        if bg_data is not None:
            mode, fill_rgba = bg_data
            data["background_mode"] = mode
            if fill_rgba is not None:
                data["background_color"] = fill_rgba
        else:
            data["background_mode"] = BackgroundMode.TRANSPARENT

        return data

    def individual_frames_data(self) -> dict[str, Any]:
        """Collect individual-frame export settings."""
        data: dict[str, Any] = {
            "base_name": self._widget_text_or("base_name", "frame"),
        }

        pattern_group = self._parent._settings_widgets.get("pattern_group")
        if pattern_group and pattern_group.checkedButton():
            data["pattern"] = _NAMING_PATTERNS[pattern_group.id(pattern_group.checkedButton())]
        else:
            data["pattern"] = _NAMING_PATTERNS[0]

        return data

    def selected_frames_data(self) -> dict[str, Any]:
        """Collect selected-frame export settings."""
        parent = self._parent
        selected_indices: list[int] = []
        if hasattr(parent, "frame_list"):
            selected_indices.extend(
                item.data(Qt.ItemDataRole.UserRole) for item in parent.frame_list.selectedItems()
            )

        return {
            "selected_indices": selected_indices,
            "base_name": self._widget_text_or("selected_base_name", "frame"),
            "pattern": _NAMING_PATTERNS[0],
        }

    def layout_mode(self) -> LayoutMode:
        """Return the currently selected sheet layout mode."""
        mode_group = self._parent._settings_widgets.get("layout_mode")
        if mode_group is not None:
            checked_id = mode_group.checkedId()
            if 0 <= checked_id < len(_LAYOUT_MODES):
                return _LAYOUT_MODES[checked_id]
        return LayoutMode.AUTO

    def _widget_text_or(self, widget_key: str, fallback: str) -> str:
        """Get text from a settings widget, falling back if absent or empty."""
        widget = self._parent._settings_widgets.get(widget_key)
        if widget and hasattr(widget, "text"):
            text = widget.text()
            if text:
                return text
        return fallback


class _ExportSettingsSummary:
    """Build the compact summary text displayed at the bottom of the settings step."""

    def __init__(self, parent: _ModernExportSettings) -> None:
        self._parent = parent

    def text(self, preset: ExportPreset | None) -> str:
        """Return summary text for the current shared and mode-specific settings."""
        parent = self._parent
        parts: list[str] = []

        output = parent.path_edit.text()
        if output:
            if len(output) > 40:
                output = "..." + output[-37:]
            parts.append(f"📁 {output}")

        fmt: str = parent.format_combo.currentText()
        scale = parent.scale_group.checkedId() if parent.scale_group.checkedButton() else 1
        parts.append(f"{fmt} @ {scale}x")

        if preset is not None:
            if preset.mode is ExportMode.SPRITE_SHEET:
                widget = parent._settings_widgets.get("sheet_filename")
                filename = widget.text() if widget is not None else ""
                if filename:
                    parts.append(f"→ {filename}.{fmt.lower()}")
            elif preset.mode is ExportMode.SELECTED_FRAMES:
                count = (
                    len(parent.frame_list.selectedItems()) if hasattr(parent, "frame_list") else 0
                )
                parts.append(f"({count} frames)")

        return " • ".join(parts)
