"""
Animation Segment Manager - Data model and persistence for animation segments
Manages animation segments with save/load functionality and validation.
Part of Animation Splitting Feature implementation.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPixmap

from config import Config


@dataclass
class AnimationSegmentData:
    """Data structure for animation segment with serialization support."""
    name: str
    start_frame: int
    end_frame: int
    color_rgb: Tuple[int, int, int] = (100, 150, 200)
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @property
    def frame_count(self) -> int:
        """Get number of frames in this segment."""
        return self.end_frame - self.start_frame + 1
    
    @property
    def color(self) -> QColor:
        """Get QColor from RGB tuple."""
        return QColor(*self.color_rgb)
    
    def set_color(self, color: QColor):
        """Set color from QColor."""
        self.color_rgb = (color.red(), color.green(), color.blue())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationSegmentData':
        """Create from dictionary."""
        return cls(**data)
    
    def validate(self, max_frames: int = None) -> Tuple[bool, str]:
        """
        Validate segment data.
        
        Args:
            max_frames: Maximum number of frames available
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.name.strip():
            return False, "Segment name cannot be empty"
        
        if self.start_frame < 0:
            return False, "Start frame cannot be negative"
        
        if self.end_frame < self.start_frame:
            return False, "End frame must be >= start frame"
        
        if max_frames is not None:
            if self.start_frame >= max_frames:
                return False, f"Start frame {self.start_frame} exceeds available frames ({max_frames})"
            
            if self.end_frame >= max_frames:
                return False, f"End frame {self.end_frame} exceeds available frames ({max_frames})"
        
        return True, ""


class AnimationSegmentManager(QObject):
    """Manages animation segments with persistence and validation."""
    
    # Signals
    segmentAdded = Signal(AnimationSegmentData)
    segmentRemoved = Signal(str)  # segment_name
    segmentUpdated = Signal(AnimationSegmentData)
    segmentsCleared = Signal()
    
    def __init__(self):
        super().__init__()
        self._segments: Dict[str, AnimationSegmentData] = {}
        self._sprite_sheet_path: str = ""
        self._max_frames: int = 0
        self._auto_save_enabled: bool = True
        
    def set_sprite_context(self, sprite_sheet_path: str, frame_count: int):
        """
        Set the current sprite sheet context.
        
        Args:
            sprite_sheet_path: Path to the sprite sheet file
            frame_count: Number of frames in the sprite sheet
        """
        if sprite_sheet_path != self._sprite_sheet_path:
            # Clear existing segments when switching sprite sheets
            self.clear_segments()
            
        self._sprite_sheet_path = sprite_sheet_path
        self._max_frames = frame_count
        
        # Try to load existing segments for this sprite sheet
        if sprite_sheet_path:
            self._load_segments_for_sprite()
    
    def add_segment(self, name: str, start_frame: int, end_frame: int, 
                   color: QColor = None, description: str = "") -> Tuple[bool, str]:
        """
        Add a new animation segment.
        
        Args:
            name: Unique name for the segment
            start_frame: Starting frame index
            end_frame: Ending frame index  
            color: Color for visualization (auto-generated if None)
            description: Optional description
            
        Returns:
            Tuple of (success, error_message)
        """
        # Validate name uniqueness
        if name in self._segments:
            return False, f"Segment '{name}' already exists"
        
        # Create segment data
        if color is None:
            # Auto-generate color based on name hash
            hash_val = abs(hash(name)) % 360
            color = QColor.fromHsv(hash_val, 180, 200)
        
        segment = AnimationSegmentData(
            name=name,
            start_frame=start_frame,
            end_frame=end_frame,
            description=description
        )
        segment.set_color(color)
        
        # Validate segment
        is_valid, error = segment.validate(self._max_frames)
        if not is_valid:
            return False, error
        
        # Add segment
        self._segments[name] = segment
        self.segmentAdded.emit(segment)
        
        # Auto-save if enabled
        if self._auto_save_enabled:
            self._auto_save()
        
        return True, ""
    
    def remove_segment(self, name: str) -> bool:
        """
        Remove an animation segment.
        
        Args:
            name: Name of segment to remove
            
        Returns:
            True if segment was removed, False if not found
        """
        if name in self._segments:
            del self._segments[name]
            self.segmentRemoved.emit(name)
            
            # Auto-save if enabled
            if self._auto_save_enabled:
                self._auto_save()
            
            return True
        return False
    
    def update_segment(self, name: str, start_frame: int = None, end_frame: int = None,
                      new_name: str = None, color: QColor = None, 
                      description: str = None) -> Tuple[bool, str]:
        """
        Update an existing animation segment.
        
        Args:
            name: Current name of the segment
            start_frame: New start frame (optional)
            end_frame: New end frame (optional)
            new_name: New name (optional)
            color: New color (optional)
            description: New description (optional)
            
        Returns:
            Tuple of (success, error_message)
        """
        if name not in self._segments:
            return False, f"Segment '{name}' not found"
        
        segment = self._segments[name]
        
        # Check for name conflicts
        if new_name and new_name != name and new_name in self._segments:
            return False, f"Segment '{new_name}' already exists"
        
        # Update fields
        if start_frame is not None:
            segment.start_frame = start_frame
        if end_frame is not None:
            segment.end_frame = end_frame
        if new_name is not None:
            segment.name = new_name
        if color is not None:
            segment.set_color(color)
        if description is not None:
            segment.description = description
        
        # Validate updated segment
        is_valid, error = segment.validate(self._max_frames)
        if not is_valid:
            return False, error
        
        # Handle name change
        if new_name and new_name != name:
            del self._segments[name]
            self._segments[new_name] = segment
            self.segmentRemoved.emit(name)
            self.segmentAdded.emit(segment)
        else:
            self.segmentUpdated.emit(segment)
        
        # Auto-save if enabled
        if self._auto_save_enabled:
            self._auto_save()
        
        return True, ""
    
    def get_segment(self, name: str) -> Optional[AnimationSegmentData]:
        """Get a segment by name."""
        return self._segments.get(name)
    
    def get_all_segments(self) -> List[AnimationSegmentData]:
        """Get all segments as a list."""
        return list(self._segments.values())
    
    def get_segment_names(self) -> List[str]:
        """Get all segment names."""
        return list(self._segments.keys())
    
    def clear_segments(self):
        """Clear all segments."""
        self._segments.clear()
        self.segmentsCleared.emit()
        
        if self._auto_save_enabled:
            self._auto_save()
    
    def has_overlapping_segments(self) -> List[Tuple[str, str]]:
        """
        Check for overlapping segments.
        
        Returns:
            List of tuples containing overlapping segment names
        """
        overlaps = []
        segments = list(self._segments.values())
        
        for i, seg1 in enumerate(segments):
            for seg2 in segments[i+1:]:
                # Check if segments overlap
                if (seg1.start_frame <= seg2.end_frame and 
                    seg2.start_frame <= seg1.end_frame):
                    overlaps.append((seg1.name, seg2.name))
        
        return overlaps
    
    def get_segments_containing_frame(self, frame_index: int) -> List[str]:
        """Get names of all segments containing the given frame."""
        return [
            name for name, segment in self._segments.items()
            if segment.start_frame <= frame_index <= segment.end_frame
        ]
    
    def extract_frames_for_segment(self, segment_name: str, 
                                 all_frames: List[QPixmap]) -> List[QPixmap]:
        """
        Extract frames for a specific segment.
        
        Args:
            segment_name: Name of the segment
            all_frames: List of all available frames
            
        Returns:
            List of frames for the segment
        """
        segment = self.get_segment(segment_name)
        if not segment:
            return []
        
        start = max(0, segment.start_frame)
        end = min(len(all_frames) - 1, segment.end_frame)
        
        return all_frames[start:end + 1]
    
    def _get_segments_file_path(self) -> str:
        """Get the file path for saving segments."""
        if not self._sprite_sheet_path:
            return ""
        
        sprite_path = Path(self._sprite_sheet_path)
        segments_dir = sprite_path.parent / ".sprite_segments"
        segments_dir.mkdir(exist_ok=True)
        
        segments_file = segments_dir / f"{sprite_path.stem}_segments.json"
        return str(segments_file)
    
    def save_segments_to_file(self, file_path: str = None) -> Tuple[bool, str]:
        """
        Save segments to JSON file.
        
        Args:
            file_path: Custom file path (uses auto-generated if None)
            
        Returns:
            Tuple of (success, error_message)
        """
        if file_path is None:
            file_path = self._get_segments_file_path()
        
        if not file_path:
            return False, "No sprite sheet loaded"
        
        try:
            data = {
                "sprite_sheet_path": self._sprite_sheet_path,
                "max_frames": self._max_frames,
                "segments": [segment.to_dict() for segment in self._segments.values()]
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to save segments: {str(e)}"
    
    def load_segments_from_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Load segments from JSON file.
        
        Args:
            file_path: File path to load from
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Clear existing segments
            self.clear_segments()
            
            # Load segments
            for segment_data in data.get("segments", []):
                segment = AnimationSegmentData.from_dict(segment_data)
                
                # Validate against current context
                is_valid, error = segment.validate(self._max_frames)
                if is_valid:
                    self._segments[segment.name] = segment
                    self.segmentAdded.emit(segment)
            
            return True, ""
            
        except Exception as e:
            return False, f"Failed to load segments: {str(e)}"
    
    def _load_segments_for_sprite(self):
        """Load segments for the current sprite sheet if they exist."""
        segments_file = self._get_segments_file_path()
        if segments_file and os.path.exists(segments_file):
            self.load_segments_from_file(segments_file)
    
    def _auto_save(self):
        """Auto-save segments if enabled and sprite sheet is loaded."""
        if self._auto_save_enabled and self._sprite_sheet_path:
            self.save_segments_to_file()
    
    def set_auto_save_enabled(self, enabled: bool):
        """Enable or disable auto-save functionality."""
        self._auto_save_enabled = enabled
    
    def export_segments_list(self) -> List[Dict[str, Any]]:
        """Export segments as a list of dictionaries for external use."""
        return [
            {
                "name": segment.name,
                "start_frame": segment.start_frame,
                "end_frame": segment.end_frame,
                "frame_count": segment.frame_count,
                "description": segment.description,
                "tags": segment.tags.copy()
            }
            for segment in self._segments.values()
        ]