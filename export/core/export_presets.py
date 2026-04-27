"""Export Presets System - predefined export configurations."""

from dataclasses import dataclass

from .frame_exporter import BackgroundMode, ExportMode, LayoutMode, SpriteSheetLayout


@dataclass
class ExportPreset:
    """Defines an export preset configuration."""

    name: str
    display_name: str
    icon: str  # Unicode emoji or icon identifier
    description: str
    mode: ExportMode
    format: str
    scale: float
    use_cases: list[str]  # Examples of when to use this preset
    sprite_sheet_layout: SpriteSheetLayout | None = None
    short_description: str | None = None


# All available presets keyed by name
PRESETS: dict[str, ExportPreset] = {
    "individual_frames": ExportPreset(
        name="individual_frames",
        display_name="Individual Frames",
        icon="📁",
        description="Export frames as separate PNG files",
        mode=ExportMode.INDIVIDUAL_FRAMES,
        format="PNG",
        scale=1.0,
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
        mode=ExportMode.SPRITE_SHEET,
        format="PNG",
        scale=1.0,
        use_cases=["Web games", "Texture atlases", "CSS sprites", "Unity animations"],
        sprite_sheet_layout=SpriteSheetLayout(
            mode=LayoutMode.AUTO, spacing=0, padding=0, background_mode=BackgroundMode.TRANSPARENT
        ),
        short_description="Optimized for game engines",
    ),
    "selected_frames": ExportPreset(
        name="selected_frames",
        display_name="Selected Frames",
        icon="🎯",
        description="Export only specific frames you choose",
        mode=ExportMode.SELECTED_FRAMES,
        format="PNG",
        scale=1.0,
        use_cases=["Key frames", "Specific poses", "Reference frames", "Partial exports"],
        short_description="Export specific frames",
    ),
    "segments_per_row": ExportPreset(
        name="segments_per_row",
        display_name="Segments Per Row",
        icon="🎬",
        description="Export sprite sheet with each segment on its own row",
        mode=ExportMode.SEGMENTS_SHEET,
        format="PNG",
        scale=1.0,
        use_cases=[
            "Game engines",
            "Animation tools",
            "Organized sprite sheets",
            "State-based animations",
        ],
        sprite_sheet_layout=SpriteSheetLayout(
            mode=LayoutMode.SEGMENTS_PER_ROW,
            spacing=0,
            padding=0,
            background_mode=BackgroundMode.TRANSPARENT,
        ),
        short_description="One row per animation",
    ),
}


def get_preset(name: str) -> ExportPreset | None:
    """Get a preset by name."""
    return PRESETS.get(name)
