"""Export Presets System - predefined export configurations."""

from dataclasses import dataclass
from typing import Any

from .frame_exporter import SpriteSheetLayout


@dataclass
class ExportPreset:
    """Defines an export preset configuration."""

    name: str
    display_name: str
    icon: str  # Unicode emoji or icon identifier
    description: str
    mode: str  # ExportMode value
    format: str
    scale: float
    default_pattern: str
    tooltip: str
    use_cases: list[str]  # Examples of when to use this preset
    sprite_sheet_layout: SpriteSheetLayout | None = None
    short_description: str | None = None

    def get_settings_dict(self) -> dict[str, Any]:
        """Convert preset to settings dictionary."""
        settings = {
            "mode": self.mode,
            "format": self.format,
            "scale_factor": self.scale,
            "pattern": self.default_pattern,
            "preset_name": self.name,
        }
        if self.sprite_sheet_layout is not None:
            settings["sprite_sheet_layout"] = self.sprite_sheet_layout
        return settings


# All available presets keyed by name
PRESETS: dict[str, ExportPreset] = {
    "individual_frames": ExportPreset(
        name="individual_frames",
        display_name="Individual Frames",
        icon="📁",
        description="Export frames as separate PNG files",
        mode="individual",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_{index:03d}",
        tooltip="Export frames individually - choose all frames or selected frames in the dialog",
        use_cases=[
            "Game assets",
            "Video editing",
            "Frame analysis",
            "Individual editing",
            "Key frames",
            "Specific poses",
        ],
        short_description="Perfect for editing",
    ),
    "sprite_sheet": ExportPreset(
        name="sprite_sheet",
        display_name="Sprite Sheet",
        icon="📋",
        description="Combine all frames into a single image",
        mode="sheet",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_sheet",
        tooltip="Ideal for web games, texture atlases, and reducing file count",
        use_cases=["Web games", "Texture atlases", "CSS sprites", "Unity animations"],
        sprite_sheet_layout=SpriteSheetLayout(
            mode="auto", spacing=0, padding=0, background_mode="transparent"
        ),
        short_description="Optimized for game engines",
    ),
    "web_optimized": ExportPreset(
        name="web_optimized",
        display_name="Web Optimized",
        icon="🌐",
        description="Smaller files optimized for web use",
        mode="individual",
        format="PNG",
        scale=0.5,
        default_pattern="{name}_web_{index:03d}",
        tooltip="Reduced size frames perfect for web galleries and responsive design",
        use_cases=["Web galleries", "Mobile apps", "Email attachments", "Fast loading"],
    ),
    "print_quality": ExportPreset(
        name="print_quality",
        display_name="Print Quality",
        icon="🖨️",
        description="High resolution for printing",
        mode="individual",
        format="PNG",
        scale=2.0,
        default_pattern="{name}_print_{index:03d}",
        tooltip="Double resolution frames suitable for high-quality printing",
        use_cases=["Physical prints", "High-res displays", "Detailed analysis", "Archival"],
    ),
    "web_game_atlas": ExportPreset(
        name="web_game_atlas",
        display_name="Web Game Atlas",
        icon="🎮",
        description="Compact sprite sheet optimized for web games",
        mode="sheet",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_atlas",
        tooltip="Horizontal layout with small spacing for efficient web game atlases",
        use_cases=["Web games", "HTML5 games", "CSS sprite sheets", "Mobile games"],
        sprite_sheet_layout=SpriteSheetLayout(
            mode="rows", max_columns=8, spacing=2, padding=4, background_mode="transparent"
        ),
    ),
    "spaced_sprite_sheet": ExportPreset(
        name="spaced_sprite_sheet",
        display_name="Spaced Sprite Sheet",
        icon="📐",
        description="Sprite sheet with spacing for easier editing",
        mode="sheet",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_spaced",
        tooltip="Square layout with generous spacing for easier sprite editing and analysis",
        use_cases=["Sprite editing", "Animation analysis", "Educational materials", "Debug views"],
        sprite_sheet_layout=SpriteSheetLayout(
            mode="square", spacing=8, padding=16, background_mode="checkerboard"
        ),
    ),
    "selected_frames": ExportPreset(
        name="selected_frames",
        display_name="Selected Frames",
        icon="🎯",
        description="Export only specific frames you choose",
        mode="selected",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_selected_{index:03d}",
        tooltip="Choose specific frames to export - perfect for key frames or specific poses",
        use_cases=["Key frames", "Specific poses", "Reference frames", "Partial exports"],
        short_description="Export specific frames",
    ),
    "segments_per_row": ExportPreset(
        name="segments_per_row",
        display_name="Segments Per Row",
        icon="🎬",
        description="Export sprite sheet with each segment on its own row",
        mode="segments_sheet",
        format="PNG",
        scale=1.0,
        default_pattern="{name}_segments_sheet",
        tooltip="Creates a sprite sheet where each animation segment (walk, run, jump) is on its own row",
        use_cases=[
            "Game engines",
            "Animation tools",
            "Organized sprite sheets",
            "State-based animations",
        ],
        sprite_sheet_layout=SpriteSheetLayout(
            mode="segments_per_row", spacing=0, padding=0, background_mode="transparent"
        ),
        short_description="One row per animation",
    ),
}


def get_preset(name: str) -> ExportPreset | None:
    """Get a preset by name."""
    return PRESETS.get(name)


def get_all_presets() -> list[ExportPreset]:
    """Get all available presets."""
    return list(PRESETS.values())
