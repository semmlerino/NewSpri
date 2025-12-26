"""
Animation Segment Manager - Data model and persistence for animation segments
Manages animation segments with save/load functionality and validation.
Part of Animation Splitting Feature implementation.
"""

import contextlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPixmap


@dataclass
class AnimationSegmentData:
    """Data structure for animation segment with serialization support."""
    name: str
    start_frame: int
    end_frame: int
    color_rgb: tuple[int, int, int] = (100, 150, 200)
    description: str = ""
    tags: list[str] | None = None
    bounce_mode: bool = False  # Play forward then backward
    frame_holds: dict[int, int] | None = None  # Frame index -> hold duration in frames

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.frame_holds is None:
            self.frame_holds = {}

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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AnimationSegmentData':
        """Create from dictionary."""
        # Handle backward compatibility for segments without new fields
        data = data.copy()
        if 'bounce_mode' not in data:
            data['bounce_mode'] = False
        if 'frame_holds' not in data:
            data['frame_holds'] = {}
        # Convert frame_holds keys from strings to ints (JSON serializes dict keys as strings)
        if isinstance(data.get('frame_holds'), dict):
            data['frame_holds'] = {int(k): v for k, v in data['frame_holds'].items()}
        return cls(**data)

    def validate(self, max_frames: int | None = None) -> tuple[bool, str]:
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
        self._segments: dict[str, AnimationSegmentData] = {}
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
            # Temporarily disable auto-save to prevent saving empty segments to old file
            was_auto_save_enabled = self._auto_save_enabled
            self._auto_save_enabled = False
            self.clear_segments()
            self._auto_save_enabled = was_auto_save_enabled

        self._sprite_sheet_path = sprite_sheet_path
        self._max_frames = frame_count

        # Try to load existing segments for this sprite sheet
        if sprite_sheet_path:
            self._load_segments_for_sprite()

    def add_segment(self, name: str, start_frame: int, end_frame: int,
                   color: QColor | None = None, description: str = "") -> tuple[bool, str]:
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

        # Check for overlapping segments
        overlapping = self._find_overlapping_segment(start_frame, end_frame)
        if overlapping:
            return False, f"Frames {start_frame}-{end_frame} overlap with segment '{overlapping}'"

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

    def update_segment(self, name: str, start_frame: int | None = None, end_frame: int | None = None,
                      new_name: str | None = None, color: QColor | None = None,
                      description: str | None = None) -> tuple[bool, str]:
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

    def rename_segment(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """
        Rename an animation segment.

        Args:
            old_name: Current name of the segment
            new_name: New name for the segment

        Returns:
            Tuple of (success, error_message)
        """
        return self.update_segment(old_name, new_name=new_name)

    def set_bounce_mode(self, segment_name: str, bounce_mode: bool) -> tuple[bool, str]:
        """
        Set bounce mode for a segment.

        Args:
            segment_name: Name of the segment
            bounce_mode: Whether to use bounce/ping-pong animation

        Returns:
            Tuple of (success, error_message)
        """
        if segment_name not in self._segments:
            return False, f"Segment '{segment_name}' not found"

        self._segments[segment_name].bounce_mode = bounce_mode

        # Auto-save if enabled
        if self._auto_save_enabled:
            self._auto_save()

        return True, ""

    def set_frame_holds(self, segment_name: str, frame_holds: dict[int, int]) -> tuple[bool, str]:
        """
        Set frame holds for a segment.

        Args:
            segment_name: Name of the segment
            frame_holds: Dictionary mapping frame indices to hold durations

        Returns:
            Tuple of (success, error_message)
        """
        if segment_name not in self._segments:
            return False, f"Segment '{segment_name}' not found"

        # Validate frame holds are within segment range
        segment = self._segments[segment_name]
        for frame_idx in frame_holds:
            if frame_idx < 0 or frame_idx >= segment.frame_count:
                return False, f"Frame index {frame_idx} is out of range for segment"

        segment.frame_holds = frame_holds

        # Auto-save if enabled
        if self._auto_save_enabled:
            self._auto_save()

        return True, ""

    def get_segment(self, name: str) -> AnimationSegmentData | None:
        """Get a segment by name."""
        return self._segments.get(name)

    def get_all_segments(self) -> list[AnimationSegmentData]:
        """Get all segments as a list."""
        return list(self._segments.values())

    def get_segment_names(self) -> list[str]:
        """Get all segment names."""
        return list(self._segments.keys())

    def clear_segments(self):
        """Clear all segments."""
        self._segments.clear()
        self.segmentsCleared.emit()

        if self._auto_save_enabled:
            self._auto_save()

    def has_overlapping_segments(self) -> list[tuple[str, str]]:
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

    def _find_overlapping_segment(self, start_frame: int, end_frame: int) -> str | None:
        """
        Find if a frame range overlaps with any existing segment.

        Args:
            start_frame: Start of the range to check
            end_frame: End of the range to check

        Returns:
            Name of the first overlapping segment, or None if no overlap
        """
        for segment in self._segments.values():
            # Check if ranges overlap using interval overlap logic
            if start_frame <= segment.end_frame and segment.start_frame <= end_frame:
                return segment.name
        return None

    def get_segments_containing_frame(self, frame_index: int) -> list[str]:
        """Get names of all segments containing the given frame."""
        return [
            name for name, segment in self._segments.items()
            if segment.start_frame <= frame_index <= segment.end_frame
        ]

    def get_segment_at_frame(self, frame_index: int) -> AnimationSegmentData | None:
        """Get the first segment that contains a specific frame."""
        for _name, segment in self._segments.items():
            if segment.start_frame <= frame_index <= segment.end_frame:
                return segment
        return None

    def get_segments(self) -> list[AnimationSegmentData]:
        """Alias for get_all_segments() for backward compatibility."""
        return self.get_all_segments()

    def extract_frames_for_segment(self, segment_name: str,
                                 all_frames: list[QPixmap]) -> list[QPixmap]:
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

    def save_segments_to_file(self, file_path: str | None = None) -> tuple[bool, str]:
        """
        Save segments to JSON file using atomic write pattern.

        Args:
            file_path: Custom file path (uses auto-generated if None)

        Returns:
            Tuple of (success, error_message)
        """
        if file_path is None:
            file_path = self._get_segments_file_path()

        if not file_path:
            return False, "No sprite sheet loaded"

        temp_path: str | None = None
        try:
            data = {
                "sprite_sheet_path": self._sprite_sheet_path,
                "max_frames": self._max_frames,
                "segments": [segment.to_dict() for segment in self._segments.values()]
            }

            # Atomic write: write to temp file, then rename
            dir_path = os.path.dirname(file_path)
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=dir_path,
                delete=False,
                suffix='.tmp'
            ) as f:
                json.dump(data, f, indent=2)
                temp_path = f.name

            # Atomic rename (works on POSIX and Windows)
            os.replace(temp_path, file_path)

            return True, ""

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path is not None:
                # SIM105: Use contextlib.suppress instead of try/except/pass
                with contextlib.suppress(OSError):
                    os.unlink(temp_path)
            return False, f"Failed to save segments: {e!s}"

    def load_segments_from_file(self, file_path: str) -> tuple[bool, str]:
        """
        Load segments from JSON file.

        Args:
            file_path: File path to load from

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(file_path) as f:
                data = json.load(f)

            segments_in_file = data.get("segments", [])

            # Clear existing segments
            # Temporarily disable auto-save to prevent overwriting the file we're loading
            was_auto_save_enabled = self._auto_save_enabled
            self._auto_save_enabled = False
            self.clear_segments()
            self._auto_save_enabled = was_auto_save_enabled

            # Load segments and track any that are skipped
            loaded_count = 0
            skipped_segments: list[tuple[str, str]] = []

            for segment_data in segments_in_file:
                segment = AnimationSegmentData.from_dict(segment_data)

                # Validate against current context
                is_valid, error = segment.validate(self._max_frames)
                if is_valid:
                    self._segments[segment.name] = segment
                    self.segmentAdded.emit(segment)
                    loaded_count += 1
                else:
                    skipped_segments.append((segment.name, error))

            # Report results including any skipped segments
            if skipped_segments:
                skipped_names = [name for name, _ in skipped_segments[:3]]
                summary = ", ".join(skipped_names)
                if len(skipped_segments) > 3:
                    summary += f" (and {len(skipped_segments) - 3} more)"
                return True, f"Loaded {loaded_count} segments. Skipped {len(skipped_segments)}: {summary}"

            return True, ""

        except Exception as e:
            return False, f"Failed to load segments: {e!s}"

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

    def export_segments_list(self) -> list[dict[str, Any]]:
        """Export segments as a list of dictionaries for external use."""
        return [
            {
                "name": segment.name,
                "start_frame": segment.start_frame,
                "end_frame": segment.end_frame,
                "frame_count": segment.frame_count,
                "description": segment.description,
                "tags": segment.tags.copy() if segment.tags else []
            }
            for segment in self._segments.values()
        ]
