"""
Export Presets System
Provides predefined export configurations for common use cases.
Part of Phase 1: Export Dialog Redesign implementation.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import os

from config import Config
from .frame_exporter import SpriteSheetLayout


class ExportPresetType(Enum):
    """Types of export presets available."""
    INDIVIDUAL_FRAMES = "individual_frames"
    SPRITE_SHEET = "sprite_sheet"
    WEB_OPTIMIZED = "web_optimized"
    PRINT_QUALITY = "print_quality"
    ANIMATION_SEGMENTS = "animation_segments"
    WEB_GAME_ATLAS = "web_game_atlas"
    SPACED_SPRITE_SHEET = "spaced_sprite_sheet"
    PRINT_ATLAS = "print_atlas"
    SELECTED_FRAMES = "selected_frames"
    STANDARD = "standard"  # For categorizing presets
    CUSTOM = "custom"


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
    use_cases: List[str]  # Examples of when to use this preset
    estimated_size_multiplier: float = 1.0  # Rough size estimate multiplier
    sprite_sheet_layout: Optional[SpriteSheetLayout] = None  # Layout configuration for sprite sheets
    short_description: Optional[str] = None  # Brief description for UI cards
    recommended_for: Optional[List[str]] = None  # Bullet points for recommendations
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """Convert preset to settings dictionary."""
        settings = {
            'mode': self.mode,
            'format': self.format,
            'scale_factor': self.scale,
            'pattern': self.default_pattern,
            'preset_name': self.name
        }
        
        # Include sprite sheet layout if available
        if self.sprite_sheet_layout is not None:
            settings['sprite_sheet_layout'] = self.sprite_sheet_layout
            
        return settings


class ExportPresetManager:
    """Manages export presets and quick export functionality."""
    
    # Built-in presets with comprehensive configurations
    BUILTIN_PRESETS = {
        ExportPresetType.INDIVIDUAL_FRAMES: ExportPreset(
            name="individual_frames",
            display_name="Individual Frames",
            icon="📁",
            description="Export frames as separate PNG files",
            mode="individual",
            format="PNG",
            scale=1.0,
            default_pattern="{name}_{index:03d}",
            tooltip="Export frames individually - choose all frames or selected frames in the dialog",
            use_cases=["Game assets", "Video editing", "Frame analysis", "Individual editing", "Key frames", "Specific poses"],
            estimated_size_multiplier=1.0,
            short_description="Perfect for editing",
            recommended_for=["Individual frame editing", "Video production", "Asset libraries"]
        ),
        
        ExportPresetType.SPRITE_SHEET: ExportPreset(
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
            estimated_size_multiplier=0.8,  # Usually smaller due to efficient packing
            sprite_sheet_layout=SpriteSheetLayout(
                mode='auto',
                spacing=0,
                padding=0,
                background_mode='transparent'
            ),
            short_description="Optimized for game engines",
            recommended_for=["Game development", "Web animations", "Texture atlases"]
        ),
        
        ExportPresetType.WEB_OPTIMIZED: ExportPreset(
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
            estimated_size_multiplier=0.25
        ),
        
        ExportPresetType.PRINT_QUALITY: ExportPreset(
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
            estimated_size_multiplier=4.0  # 2x scale = 4x pixels
        ),
        
        ExportPresetType.ANIMATION_SEGMENTS: ExportPreset(
            name="animation_segments",
            display_name="Animation Segments",
            icon="🎭",
            description="Export animation segments separately",
            mode="segments",
            format="PNG",
            scale=1.0,
            default_pattern="{segment}_{frame:03d}",
            tooltip="Export animation segments as separate collections with metadata",
            use_cases=["Character animations", "State machines", "Animation libraries", "Game assets"],
            estimated_size_multiplier=1.0
        ),
        
        # Enhanced sprite sheet presets with layout configurations
        ExportPresetType.WEB_GAME_ATLAS: ExportPreset(
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
            estimated_size_multiplier=0.75,
            sprite_sheet_layout=SpriteSheetLayout(
                mode='rows',
                max_columns=8,
                spacing=2,
                padding=4,
                background_mode='transparent'
            )
        ),
        
        ExportPresetType.SPACED_SPRITE_SHEET: ExportPreset(
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
            estimated_size_multiplier=1.2,
            sprite_sheet_layout=SpriteSheetLayout(
                mode='square',
                spacing=8,
                padding=16,
                background_mode='checkerboard'
            )
        ),
        
        ExportPresetType.PRINT_ATLAS: ExportPreset(
            name="print_atlas",
            display_name="Print Atlas",
            icon="📰",
            description="High quality sprite sheet for printing",
            mode="sheet",
            format="PNG",
            scale=2.0,
            default_pattern="{name}_print_atlas",
            tooltip="High resolution sprite sheet with white background and padding for printing",
            use_cases=["Physical prints", "Documentation", "Portfolios", "Archival purposes"],
            estimated_size_multiplier=3.5,
            sprite_sheet_layout=SpriteSheetLayout(
                mode='square',
                spacing=12,
                padding=24,
                background_mode='solid',
                background_color=(255, 255, 255, 255)
            )
        ),
        
        ExportPresetType.SELECTED_FRAMES: ExportPreset(
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
            estimated_size_multiplier=1.0,
            short_description="Export specific frames",
            recommended_for=["Key frame extraction", "Reference images", "Selective export"]
        )
    }
    
    def __init__(self):
        """Initialize preset manager."""
        self._custom_presets: Dict[str, ExportPreset] = {}
        self._load_custom_presets()
    
    def get_preset(self, preset_type_or_name) -> Optional[ExportPreset]:
        """Get a preset by type or name."""
        # Handle ExportPresetType
        if isinstance(preset_type_or_name, ExportPresetType):
            return self.BUILTIN_PRESETS.get(preset_type_or_name)
        
        # Handle string name
        if isinstance(preset_type_or_name, str):
            # Check built-in presets
            for preset in self.BUILTIN_PRESETS.values():
                if preset.name == preset_type_or_name:
                    return preset
            # Check custom presets
            return self._custom_presets.get(preset_type_or_name)
        
        return None
    
    def get_all_presets(self) -> List[ExportPreset]:
        """Get all available presets (built-in + custom)."""
        presets = list(self.BUILTIN_PRESETS.values())
        presets.extend(self._custom_presets.values())
        return presets
    
    def get_builtin_presets(self) -> List[ExportPreset]:
        """Get only built-in presets."""
        return list(self.BUILTIN_PRESETS.values())
    
    def get_presets_by_type(self, preset_type: ExportPresetType) -> List[ExportPreset]:
        """Get presets by type (e.g., STANDARD for main presets)."""
        if preset_type == ExportPresetType.STANDARD:
            # Return the main 4 presets for the wizard
            return [
                self.BUILTIN_PRESETS.get(ExportPresetType.INDIVIDUAL_FRAMES),
                self.BUILTIN_PRESETS.get(ExportPresetType.SPRITE_SHEET),
                self.BUILTIN_PRESETS.get(ExportPresetType.SELECTED_FRAMES)
            ]
        elif preset_type == ExportPresetType.CUSTOM:
            return list(self._custom_presets.values())
        else:
            # Return preset matching the specific type
            preset = self.BUILTIN_PRESETS.get(preset_type)
            return [preset] if preset else []
    
    def add_custom_preset(self, preset: ExportPreset) -> bool:
        """Add a custom preset."""
        try:
            self._custom_presets[preset.name] = preset
            self._save_custom_presets()
            return True
        except Exception:
            return False
    
    def remove_custom_preset(self, name: str) -> bool:
        """Remove a custom preset."""
        if name in self._custom_presets:
            del self._custom_presets[name]
            self._save_custom_presets()
            return True
        return False
    
    def estimate_output_size(self, preset: ExportPreset, frame_count: int, 
                           avg_frame_size_kb: float = 50.0) -> Dict[str, Any]:
        """Estimate output size and file count for a preset."""
        base_size_kb = avg_frame_size_kb * preset.estimated_size_multiplier * (preset.scale ** 2)
        
        if preset.mode == "individual":
            file_count = frame_count
            total_size_kb = base_size_kb * frame_count
        elif preset.mode == "sheet":
            file_count = 1
            total_size_kb = base_size_kb * frame_count * 0.8  # Sprite sheets are more efficient
            
            # Account for spacing and padding overhead in sprite sheets
            if preset.sprite_sheet_layout:
                layout = preset.sprite_sheet_layout
                if layout.spacing > 0:
                    total_size_kb *= Config.Export.SPACING_SIZE_FACTOR
                if layout.padding > 0:
                    total_size_kb *= Config.Export.PADDING_SIZE_FACTOR
                    
        elif preset.mode == "gif":
            file_count = 1
            total_size_kb = base_size_kb * frame_count * 0.3  # GIF compression
        else:
            file_count = frame_count
            total_size_kb = base_size_kb * frame_count
        
        return {
            'file_count': file_count,
            'total_size_kb': total_size_kb,
            'total_size_mb': total_size_kb / 1024,
            'avg_file_size_kb': total_size_kb / file_count if file_count > 0 else 0,
            'size_category': self._get_size_category(total_size_kb)
        }
    
    def get_recommended_preset(self, frame_count: int, use_case: str = "") -> ExportPreset:
        """Get recommended preset based on frame count and use case."""
        # Simple heuristics for recommendations
        if "web" in use_case.lower() or "online" in use_case.lower():
            return self.get_preset(ExportPresetType.WEB_OPTIMIZED)
        
        if "print" in use_case.lower() or "quality" in use_case.lower():
            return self.get_preset(ExportPresetType.PRINT_QUALITY)
        
        if "game" in use_case.lower() or "atlas" in use_case.lower():
            if frame_count > 20:
                return self.get_preset(ExportPresetType.SPRITE_SHEET)
            else:
                return self.get_preset(ExportPresetType.INDIVIDUAL_FRAMES)
        
        # Default recommendation based on frame count
        if frame_count <= 20:
            return self.get_preset(ExportPresetType.INDIVIDUAL_FRAMES)
        else:
            return self.get_preset(ExportPresetType.SPRITE_SHEET)
    
    def generate_output_preview(self, preset: ExportPreset, frame_count: int, 
                              base_name: str = "frame") -> Dict[str, Any]:
        """Generate a preview of what files will be created."""
        size_info = self.estimate_output_size(preset, frame_count)
        
        if preset.mode == "individual":
            filenames = []
            for i in range(min(frame_count, 5)):  # Show first 5 examples
                filename = preset.default_pattern.format(
                    name=base_name, index=i, frame=i+1
                ) + f".{preset.format.lower()}"
                filenames.append(filename)
            
            if frame_count > 5:
                filenames.append(f"... and {frame_count - 5} more files")
                
        elif preset.mode == "sheet":
            filename = preset.default_pattern.format(name=base_name) + f".{preset.format.lower()}"
            filenames = [filename]
            
        elif preset.mode == "gif":
            filename = preset.default_pattern.format(name=base_name) + ".gif"
            filenames = [filename]
            
        else:
            filenames = ["Unknown output format"]
        
        # Add layout information for sprite sheets
        layout_info = {}
        if preset.mode == "sheet" and preset.sprite_sheet_layout:
            layout = preset.sprite_sheet_layout
            layout_info = {
                'layout_mode': layout.mode,
                'spacing': layout.spacing,
                'padding': layout.padding,
                'background': layout.background_mode
            }
        
        return {
            'filenames': filenames,
            'file_count': size_info['file_count'],
            'total_size_mb': size_info['total_size_mb'],
            'size_category': size_info['size_category'],
            'description': self._generate_preview_description(preset, size_info),
            'layout_info': layout_info
        }
    
    def _get_size_category(self, size_kb: float) -> str:
        """Categorize file size for user-friendly display."""
        if size_kb < 100:
            return "tiny"
        elif size_kb < 1024:  # < 1 MB
            return "small"
        elif size_kb < 10240:  # < 10 MB
            return "medium"
        elif size_kb < 102400:  # < 100 MB
            return "large"
        else:
            return "very_large"
    
    def _generate_preview_description(self, preset: ExportPreset, size_info: Dict[str, Any]) -> str:
        """Generate human-readable description of export output."""
        file_count = size_info['file_count']
        size_mb = size_info['total_size_mb']
        
        if file_count == 1:
            return f"Creates 1 file • ~{size_mb:.1f} MB"
        else:
            return f"Creates {file_count} files • ~{size_mb:.1f} MB total"
    
    def _load_custom_presets(self):
        """Load custom presets from user configuration."""
        # TODO: Implement custom preset persistence
        # For now, just initialize empty
        pass
    
    def _save_custom_presets(self):
        """Save custom presets to user configuration."""
        # TODO: Implement custom preset persistence
        pass


# Global instance for easy access
_preset_manager = None

def get_preset_manager() -> ExportPresetManager:
    """Get the global preset manager instance."""
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = ExportPresetManager()
    return _preset_manager


# Convenience functions
def get_preset(preset_type: ExportPresetType) -> Optional[ExportPreset]:
    """Get a preset by type."""
    return get_preset_manager().get_preset(preset_type)

def get_recommended_preset(frame_count: int, use_case: str = "") -> ExportPreset:
    """Get recommended preset for given parameters."""
    return get_preset_manager().get_recommended_preset(frame_count, use_case)

def estimate_export_size(preset: ExportPreset, frame_count: int) -> Dict[str, Any]:
    """Estimate export size for preset and frame count."""
    return get_preset_manager().estimate_output_size(preset, frame_count)