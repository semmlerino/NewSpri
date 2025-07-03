"""
Animation Grid View - Frame selection and animation splitting component
Provides a grid view of all sprite frames with selection capabilities for animation splitting.
Part of Animation Splitting Feature implementation.
"""

from typing import List, Optional, Tuple, Dict, Any, Set
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QSizePolicy, QToolTip, QMenu,
    QInputDialog, QMessageBox, QSplitter, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QMouseEvent, QContextMenuEvent

from config import Config
from utils.styles import StyleManager


@dataclass
class AnimationSegment:
    """Represents a single animation segment with start/end frames."""
    name: str
    start_frame: int
    end_frame: int
    color: QColor = None
    
    # Class variable to track color index for unique colors
    _color_index = 0
    _predefined_colors = [
        QColor("#E91E63"),  # Pink
        QColor("#9C27B0"),  # Purple
        QColor("#673AB7"),  # Deep Purple
        QColor("#3F51B5"),  # Indigo
        QColor("#2196F3"),  # Blue
        QColor("#03A9F4"),  # Light Blue
        QColor("#00BCD4"),  # Cyan
        QColor("#009688"),  # Teal
        QColor("#4CAF50"),  # Green
        QColor("#8BC34A"),  # Light Green
        QColor("#CDDC39"),  # Lime
        QColor("#FFC107"),  # Amber
        QColor("#FF9800"),  # Orange
        QColor("#FF5722"),  # Deep Orange
        QColor("#795548"),  # Brown
        QColor("#607D8B"),  # Blue Grey
    ]
    
    def __post_init__(self):
        if self.color is None:
            # Use predefined colors in sequence for better visual distinction
            self.color = AnimationSegment._predefined_colors[AnimationSegment._color_index % len(AnimationSegment._predefined_colors)]
            AnimationSegment._color_index += 1
    
    @property
    def frame_count(self) -> int:
        """Get number of frames in this segment."""
        return self.end_frame - self.start_frame + 1


class FrameThumbnail(QLabel):
    """Individual frame thumbnail widget with advanced selection capabilities."""
    
    clicked = Signal(int, int)  # frame_index, modifiers (Qt.KeyboardModifiers as int)
    doubleClicked = Signal(int)  # frame_index
    rightClicked = Signal(int, QPoint)  # frame_index, global_position
    dragStarted = Signal(int)  # frame_index
    
    def __init__(self, frame_index: int, pixmap: QPixmap, thumbnail_size: int = 80):
        super().__init__()
        self.frame_index = frame_index
        self._thumbnail_size = thumbnail_size
        self._selected = False
        self._highlighted = False  # For hover/drag-over effects
        self._is_segment_start = False
        self._is_segment_end = False
        self._segment_color = None
        
        # Mouse interaction tracking
        self._mouse_press_pos = None
        self._drag_threshold = 8  # Increased for less sensitive drag detection
        
        # Set up the thumbnail
        self._setup_thumbnail(pixmap)
        self._update_style()
    
    def _setup_thumbnail(self, pixmap: QPixmap):
        """Set up the thumbnail display."""
        if pixmap and not pixmap.isNull():
            # Scale pixmap to thumbnail size while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self._thumbnail_size, self._thumbnail_size,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        
        self.setFixedSize(self._thumbnail_size + 8, self._thumbnail_size + 8)  # +8 for border
        self.setAlignment(Qt.AlignCenter)
        self.setToolTip(f"Frame {self.frame_index}")
    
    def _update_style(self):
        """Update visual style based on selection state."""
        if self._selected:
            border_color = "#4CAF50"  # Green for selected
            border_width = "3px"
            background = "#E8F5E8"
        elif self._highlighted:
            border_color = "#2196F3"  # Blue for highlighted/drag-over
            border_width = "2px"
            background = "#E3F2FD"
        elif self._segment_color is not None and self._segment_color.isValid():
            # Enhanced segment visualization
            border_color = self._segment_color.name()
            border_width = "3px"
            # Create lighter background from segment color
            lighter_color = self._segment_color.lighter(180)
            background = lighter_color.name()
        else:
            border_color = "#CCCCCC"
            border_width = "1px"
            background = "white"  # Use named color instead of hex
        
        hover_style = ""
        if not self._selected and not self._highlighted:
            hover_style = """
            QLabel:hover {
                border-color: #2196F3;
                background-color: #F0F8FF;
            }
            """
        
        # Add segment marker overlays for start/end frames
        overlay_style = ""
        if self._is_segment_start:
            overlay_style += """
                border-left-width: 5px;
                border-left-style: solid;
            """
        if self._is_segment_end:
            overlay_style += """
                border-right-width: 5px;
                border-right-style: solid;
            """
        
        # Build the complete style
        style = f"""
            QLabel {{
                border: {border_width} solid {border_color};
                background-color: {background};
                border-radius: 4px;
                margin: 2px;
                {overlay_style}
            }}
            {hover_style}
        """
        
        self.setStyleSheet(style)
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self._selected = selected
        self._update_style()
    
    def set_highlighted(self, highlighted: bool):
        """Set highlighted state (for drag-over effects)."""
        self._highlighted = highlighted
        self._update_style()
    
    def set_segment_markers(self, is_start: bool = False, is_end: bool = False, color: QColor = None):
        """Set segment start/end markers."""
        self._is_segment_start = is_start
        self._is_segment_end = is_end
        self._segment_color = color
        
        # Update the visual style
        self._update_style()
        
        # Force visual update
        self.update()
        self.repaint()
    
    def force_clear_style(self):
        """Forcefully clear all styles and reset to default."""
        # Reset all state
        self._is_segment_start = False
        self._is_segment_end = False
        self._segment_color = None
        self._selected = False
        self._highlighted = False
        
        # Set explicit default style
        default_style = """
            QLabel {
                border: 1px solid #CCCCCC;
                background-color: rgb(255, 255, 255);
                background: rgb(255, 255, 255);
                border-radius: 4px;
                margin: 2px;
            }
            QLabel:hover {
                border-color: #2196F3;
                background-color: rgb(240, 248, 255);
            }
        """
        self.setStyleSheet(default_style)
        
        # Force update
        self.update()
        self.repaint()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events with modifier support."""
        if event.button() == Qt.LeftButton:
            self._mouse_press_pos = event.position()
            # Convert modifiers to integer safely
            try:
                # Try the newer PySide6 approach first
                modifiers_value = event.modifiers().value
            except AttributeError:
                # Fallback for older versions
                modifiers_value = int(event.modifiers())
            except TypeError:
                # If all else fails, use 0 (no modifiers)
                modifiers_value = 0
            
            self.clicked.emit(self.frame_index, modifiers_value)
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit(self.frame_index, event.globalPosition().toPoint())
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click for frame preview."""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.frame_index)
        super().mouseDoubleClickEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for drag detection."""
        if (event.buttons() & Qt.LeftButton and 
            self._mouse_press_pos and
            (event.position() - self._mouse_press_pos).manhattanLength() > self._drag_threshold):
            self.dragStarted.emit(self.frame_index)
            self._mouse_press_pos = None  # Prevent multiple drag signals
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        self._mouse_press_pos = None
        super().mouseReleaseEvent(event)



class AnimationGridView(QWidget):
    """Main grid view widget for animation frame selection and splitting."""
    
    # Signals
    frameSelected = Signal(int)  # frame_index (for status updates)
    framePreviewRequested = Signal(int)  # frame_index (for double-click preview)
    selectionChanged = Signal(list)  # selected_frame_indices
    segmentCreated = Signal(AnimationSegment)  # new_segment
    segmentDeleted = Signal(str)  # segment_name
    segmentRenamed = Signal(str, str)  # old_name, new_name
    segmentSelected = Signal(AnimationSegment)  # selected_segment
    segmentPreviewRequested = Signal(AnimationSegment)  # segment_to_preview (double-click)
    exportRequested = Signal(AnimationSegment)  # segment_to_export
    
    def __init__(self):
        super().__init__()
        
        # State
        self._frames: List[QPixmap] = []
        self._thumbnails: List[FrameThumbnail] = []
        self._segments: Dict[str, AnimationSegment] = {}
        
        # Enhanced selection state
        self._selected_frames: Set[int] = set()  # All selected frame indices
        self._last_clicked_frame: Optional[int] = None  # For range selection
        self._drag_start_frame: Optional[int] = None  # For drag selection
        self._is_dragging: bool = False
        
        # UI settings
        self._grid_columns = 8
        self._thumbnail_size = 80
        
        self._setup_ui()
        self._connect_signals()
        
        # Enable mouse tracking for drag selection
        self.setMouseTracking(True)
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Just set up the grid area, no segment panel needed
        self._setup_grid_area(layout)
    
    def _setup_grid_area(self, parent_layout):
        """Set up the main grid area."""
        # Controls
        controls_layout = QHBoxLayout()
        
        self._columns_label = QLabel("Columns:")
        controls_layout.addWidget(self._columns_label)
        
        # Add column adjustment buttons
        decrease_btn = QPushButton("-")
        decrease_btn.setMaximumWidth(30)
        decrease_btn.clicked.connect(lambda: self._adjust_columns(-1))
        controls_layout.addWidget(decrease_btn)
        
        self._columns_display = QLabel(str(self._grid_columns))
        self._columns_display.setMinimumWidth(30)
        self._columns_display.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self._columns_display)
        
        increase_btn = QPushButton("+")
        increase_btn.setMaximumWidth(30)
        increase_btn.clicked.connect(lambda: self._adjust_columns(1))
        controls_layout.addWidget(increase_btn)
        
        controls_layout.addStretch()
        
        # Selection controls
        self._create_segment_btn = QPushButton("Create Animation Segment")
        self._create_segment_btn.setEnabled(False)
        self._create_segment_btn.clicked.connect(self._create_segment_from_selection)
        controls_layout.addWidget(self._create_segment_btn)
        
        self._clear_selection_btn = QPushButton("Clear Selection")
        self._clear_selection_btn.setEnabled(False)
        self._clear_selection_btn.clicked.connect(self._clear_selection)
        controls_layout.addWidget(self._clear_selection_btn)
        
        parent_layout.addLayout(controls_layout)
        
        # Add selection instructions
        instructions = QLabel(
            "Selection modes: Click = select • Drag = range • Shift+Click = extend range • "
            "Ctrl/Alt+Click = multi-select • Double-Click = preview • Right-Click = add as segment"
        )
        instructions.setStyleSheet("""
            QLabel {
                background-color: #F0F8FF;
                border: 1px solid #B0C4DE;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
                color: #2F4F4F;
            }
        """)
        instructions.setWordWrap(True)
        parent_layout.addWidget(instructions)
        
        # Scroll area for grid
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Grid container
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(2)
        
        self._scroll_area.setWidget(self._grid_container)
        parent_layout.addWidget(self._scroll_area)
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Currently no internal signals to connect as segment list is removed
        pass
    
    def set_frames(self, frames: List[QPixmap]):
        """Set the frames to display in the grid."""
        self._frames = frames
        self._clear_grid()
        self._populate_grid()
    
    def _clear_grid(self):
        """Clear the current grid."""
        for thumbnail in self._thumbnails:
            thumbnail.deleteLater()
        self._thumbnails.clear()
        
        # Clear layout
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _populate_grid(self):
        """Populate the grid with frame thumbnails."""
        for i, frame in enumerate(self._frames):
            thumbnail = FrameThumbnail(i, frame, self._thumbnail_size)
            
            # Connect new enhanced signals
            thumbnail.clicked.connect(self._on_frame_clicked)
            thumbnail.doubleClicked.connect(self._on_frame_double_clicked)
            thumbnail.rightClicked.connect(self._on_frame_right_clicked)
            thumbnail.dragStarted.connect(self._on_drag_started)
            
            row = i // self._grid_columns
            col = i % self._grid_columns
            self._grid_layout.addWidget(thumbnail, row, col)
            
            self._thumbnails.append(thumbnail)
        
        self._update_segment_visualization()
        self._update_selection_display()
    
    def _adjust_columns(self, delta: int):
        """Adjust the number of grid columns."""
        new_columns = max(1, min(20, self._grid_columns + delta))
        if new_columns != self._grid_columns:
            self._grid_columns = new_columns
            self._columns_display.setText(str(self._grid_columns))
            if self._frames:
                self._populate_grid()
    
    def _on_frame_clicked(self, frame_index: int, modifiers: int):
        """Handle frame thumbnail click with keyboard modifiers."""
        from PySide6.QtCore import Qt
        
        # Convert integer back to Qt.KeyboardModifiers for comparison
        try:
            mod_flags = Qt.KeyboardModifiers(modifiers)
        except (TypeError, ValueError):
            # If conversion fails, assume no modifiers
            mod_flags = Qt.KeyboardModifiers()
        
        if mod_flags & Qt.ControlModifier or mod_flags & Qt.AltModifier:
            # Ctrl/Alt+Click: Toggle individual frame selection
            print(f"DEBUG: Toggle selecting frame {frame_index}")
            self._toggle_frame_selection(frame_index)
        elif mod_flags & Qt.ShiftModifier and self._last_clicked_frame is not None:
            # Shift+Click: Range selection from last clicked frame
            print(f"DEBUG: Range selecting from {self._last_clicked_frame} to {frame_index}")
            self._select_frame_range(self._last_clicked_frame, frame_index)
        else:
            # Normal click: Clear previous selection and select this frame
            print(f"DEBUG: Normal click selecting frame {frame_index}")
            self._clear_selection()
            self._select_frame(frame_index)
        
        self._last_clicked_frame = frame_index
        self._update_selection_display()
        self._update_selection_controls()
        
        # Emit signal for status updates
        self.frameSelected.emit(frame_index)
        
        # Emit selection changed signal
        selected_list = list(self._selected_frames)
        print(f"DEBUG: Selection changed to {len(selected_list)} frames: {sorted(selected_list)}")
        self.selectionChanged.emit(selected_list)
    
    def _on_frame_double_clicked(self, frame_index: int):
        """Handle frame double-click for preview."""
        self.framePreviewRequested.emit(frame_index)
    
    def _on_drag_started(self, frame_index: int):
        """Handle start of drag selection."""
        self._drag_start_frame = frame_index
        self._is_dragging = True
        
        # Store current selection before starting drag
        self._pre_drag_selection = self._selected_frames.copy()
        
        # Only clear selection if this frame isn't already selected
        # This preserves existing selections when dragging from selected frames
        if frame_index not in self._selected_frames:
            self._clear_selection()
            self._select_frame(frame_index)
            # Update the pre-drag selection to reflect the new state
            self._pre_drag_selection = self._selected_frames.copy()
        else:
            # If dragging from an already selected frame, keep the selection
            print(f"DEBUG: Extending selection from frame {frame_index}")
        
        self._update_selection_display()
    
    def _toggle_frame_selection(self, frame_index: int):
        """Toggle selection of a single frame."""
        if frame_index in self._selected_frames:
            self._selected_frames.remove(frame_index)
        else:
            self._selected_frames.add(frame_index)
    
    def _select_frame(self, frame_index: int):
        """Select a single frame."""
        self._selected_frames.add(frame_index)
    
    def _select_frame_range(self, start_frame: int, end_frame: int):
        """Select a range of frames."""
        start = min(start_frame, end_frame)
        end = max(start_frame, end_frame)
        
        for i in range(start, end + 1):
            if i < len(self._thumbnails):
                self._selected_frames.add(i)
    
    def _get_segment_at_frame(self, frame_index: int) -> Optional[AnimationSegment]:
        """Get the segment that contains the given frame index."""
        for segment in self._segments.values():
            if segment.start_frame <= frame_index <= segment.end_frame:
                return segment
        return None

    def _on_frame_right_clicked(self, frame_index: int, position: QPoint):
        """Handle frame thumbnail right-click."""
        menu = QMenu(self)
        
        # Check if this frame is part of a segment
        segment = self._get_segment_at_frame(frame_index)
        
        if segment:
            # Frame is part of a segment - show segment-specific actions
            segment_menu = menu.addMenu(f"Segment: {segment.name}")
            
            # Export segment options
            export_frames_action = segment_menu.addAction("Export as Individual Frames...")
            export_frames_action.triggered.connect(
                lambda: self.exportRequested.emit(segment.name)
            )
            
            export_sheet_action = segment_menu.addAction("Export as Sprite Sheet...")
            export_sheet_action.triggered.connect(
                lambda: self.exportRequested.emit(segment.name)
            )
            
            segment_menu.addSeparator()
            
            # Rename segment action
            rename_action = segment_menu.addAction("Rename Segment...")
            rename_action.triggered.connect(
                lambda: self._prompt_rename_segment(segment.name)
            )
            
            # Delete segment action
            delete_action = segment_menu.addAction("Delete Segment")
            delete_action.triggered.connect(
                lambda: self._delete_segment(segment.name)
            )
            
            menu.addSeparator()
        
        # Add frame to selection if not already selected
        if frame_index not in self._selected_frames:
            self._clear_selection()
            self._select_frame(frame_index)
            self._update_selection_display()
        
        if self._selected_frames:
            count = len(self._selected_frames)
            sorted_frames = sorted(self._selected_frames)
            
            # Create descriptive action text
            if count == 1:
                action_text = f"Add frame {sorted_frames[0]} as animation segment"
            elif self._is_contiguous_selection(sorted_frames):
                action_text = f"Add frames {sorted_frames[0]}-{sorted_frames[-1]} as animation segment"
            else:
                action_text = f"Add {count} frames as animation segment"
            
            create_action = menu.addAction(action_text)
            create_action.triggered.connect(self._create_segment_from_selection)
            
            menu.addSeparator()
            
            # Quick preview action
            preview_action = menu.addAction("Preview selected frames")
            preview_action.triggered.connect(lambda: self._preview_selection())
        
        if menu.actions():
            menu.exec(position)
    
    def _update_selection_display(self):
        """Update visual state of all thumbnails based on current selection."""
        for i, thumbnail in enumerate(self._thumbnails):
            selected = i in self._selected_frames
            thumbnail.set_selected(selected)
    
    def _update_selection_controls(self):
        """Update state of selection control buttons."""
        has_selection = len(self._selected_frames) > 0
        self._create_segment_btn.setEnabled(has_selection)
        self._clear_selection_btn.setEnabled(has_selection)
        
        # Update button text to show selection count
        if has_selection:
            count = len(self._selected_frames)
            if count == 1:
                self._create_segment_btn.setText("Create Animation Segment (1 frame)")
            else:
                # For multi-select, show range info
                sorted_frames = sorted(self._selected_frames)
                if self._is_contiguous_selection(sorted_frames):
                    start, end = sorted_frames[0], sorted_frames[-1]
                    self._create_segment_btn.setText(f"Create Animation Segment (frames {start}-{end})")
                else:
                    self._create_segment_btn.setText(f"Create Animation Segment ({count} frames)")
        else:
            self._create_segment_btn.setText("Create Animation Segment")
    
    def _is_contiguous_selection(self, sorted_frames: List[int]) -> bool:
        """Check if the selected frames form a contiguous range."""
        if not sorted_frames:
            return False
        
        for i in range(1, len(sorted_frames)):
            if sorted_frames[i] != sorted_frames[i-1] + 1:
                return False
        return True
    
    def _clear_selection(self):
        """Clear current selection."""
        self._selected_frames.clear()
        self._last_clicked_frame = None
        self._drag_start_frame = None
        self._is_dragging = False
        
        # Clean up drag selection state
        if hasattr(self, '_pre_drag_selection'):
            delattr(self, '_pre_drag_selection')
        
        for thumbnail in self._thumbnails:
            thumbnail.set_selected(False)
        
        self._update_selection_controls()
    
    def _create_segment_from_selection(self):
        """Create an animation segment from current selection."""
        if not self._selected_frames:
            return
        
        sorted_frames = sorted(self._selected_frames)
        
        # Determine start and end frames
        if self._is_contiguous_selection(sorted_frames):
            # Contiguous selection - use actual range
            start, end = sorted_frames[0], sorted_frames[-1]
            description = f"frames {start}-{end}"
        else:
            # Non-contiguous selection - use overall range but warn user
            start, end = sorted_frames[0], sorted_frames[-1]
            description = f"{len(sorted_frames)} selected frames"
            
            # Show warning for non-contiguous selection
            reply = QMessageBox.question(
                self, "Non-contiguous Selection",
                f"You've selected {len(sorted_frames)} non-contiguous frames.\n"
                f"This will create a segment from frame {start} to {end} "
                f"(including unselected frames in between).\n\n"
                f"Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Generate unique default name
        default_name = self._generate_unique_segment_name()
        
        # Get segment name from user
        name, ok = QInputDialog.getText(
            self, "Create Animation Segment", 
            f"Enter name for {description}:",
            text=default_name
        )
        
        if ok and name.strip():
            segment = AnimationSegment(name.strip(), start, end)
            self.add_segment(segment)
            self._clear_selection()
            
            self.segmentCreated.emit(segment)
    
    def _generate_unique_segment_name(self, base_name: str = "Animation") -> str:
        """Generate a unique segment name that doesn't conflict with existing segments."""
        # Start with index 1
        index = 1
        
        # Keep incrementing until we find a unique name
        while True:
            candidate_name = f"{base_name}_{index}"
            if candidate_name not in self._segments:
                return candidate_name
            index += 1
            
            # Safety check to prevent infinite loop
            if index > 1000:
                # Use timestamp as fallback
                import time
                timestamp = int(time.time() * 1000) % 100000
                return f"{base_name}_{timestamp}"
    
    def add_segment(self, segment: AnimationSegment):
        """Add a new animation segment."""
        self._segments[segment.name] = segment
        self._update_segment_visualization()
    
    def sync_segments_with_manager(self, segment_manager):
        """Synchronize local segments with segment manager to prevent conflicts."""
        if not segment_manager:
            return
        
        # Get all segments from manager
        manager_segments = segment_manager.get_all_segments()
        
        # Clear current segments and rebuild from manager
        self._segments.clear()
        
        # Add all segments from manager to grid view
        for segment_data in manager_segments:
            # Convert segment manager data to AnimationSegment
            grid_segment = AnimationSegment(
                segment_data.name,
                segment_data.start_frame,
                segment_data.end_frame,
                segment_data.color
            )
            
            self._segments[segment_data.name] = grid_segment
        
        # Update visualization
        self._update_segment_visualization()
    
    def _delete_segment(self, segment_name: str):
        """Delete an animation segment."""
        if segment_name in self._segments:
            del self._segments[segment_name]
            self._update_segment_visualization()
            self.segmentDeleted.emit(segment_name)
    
    def _prompt_rename_segment(self, old_name: str):
        """Prompt user to rename a segment."""
        # Get new name from user
        new_name, ok = QInputDialog.getText(
            self, "Rename Segment", 
            f"Enter new name for '{old_name}':",
            text=old_name
        )
        
        if ok and new_name.strip():
            new_name = new_name.strip()
            
            # Check if new name already exists
            if new_name in self._segments and new_name != old_name:
                QMessageBox.warning(
                    self, "Name Already Exists",
                    f"A segment named '{new_name}' already exists.\nPlease choose a different name."
                )
                return
            
            # Perform the rename
            if new_name != old_name:
                self._rename_segment(old_name, new_name)
                # Emit signal to notify other components
                self.segmentRenamed.emit(old_name, new_name)
    
    def _rename_segment(self, old_name: str, new_name: str):
        """Rename an animation segment."""
        if old_name in self._segments and new_name not in self._segments:
            segment = self._segments.pop(old_name)
            segment.name = new_name
            self._segments[new_name] = segment
            self._update_segment_visualization()
    
    def _update_segment_visualization(self):
        """Update visual markers for all segments."""
        # First, forcefully clear all thumbnails to default state
        for thumbnail in self._thumbnails:
            thumbnail.force_clear_style()
        
        # Process clearing before applying new markers
        QApplication.processEvents()
        
        # Apply segment markers
        for segment in self._segments.values():
            for i in range(segment.start_frame, segment.end_frame + 1):
                if i < len(self._thumbnails):
                    is_start = (i == segment.start_frame)
                    is_end = (i == segment.end_frame)
                    self._thumbnails[i].set_segment_markers(is_start, is_end, segment.color)
        
        # Force a final refresh of the entire widget hierarchy
        self.update()
        self.repaint()
        
        # Also update the parent scroll area to ensure complete refresh
        if self._scroll_area:
            self._scroll_area.update()
            self._scroll_area.viewport().update()
        
        QApplication.processEvents()
    
    
    def _preview_selection(self):
        """Preview the currently selected frames as an animation."""
        if not self._selected_frames or not self._frames:
            return
            
        sorted_frames = sorted(self._selected_frames)
        # Create temporary segment for preview
        temp_segment = AnimationSegment(
            "Preview",
            sorted_frames[0],
            sorted_frames[-1]
        )
        self.segmentPreviewRequested.emit(temp_segment)
    
    def get_segments(self) -> List[AnimationSegment]:
        """Get all current animation segments."""
        return list(self._segments.values())
    
    def clear_segments(self):
        """Clear all animation segments."""
        self._segments.clear()
        # Reset color index for fresh color sequence
        AnimationSegment._color_index = 0
        self._update_segment_visualization()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for drag selection."""
        if self._is_dragging and self._drag_start_frame is not None:
            # Find the frame under the mouse cursor
            frame_under_mouse = self._get_frame_at_position(event.position())
            
            if frame_under_mouse is not None:
                # Update drag selection
                self._update_drag_selection(self._drag_start_frame, frame_under_mouse)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to end drag selection."""
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            self._drag_start_frame = None
            
            # Clean up drag selection state
            if hasattr(self, '_pre_drag_selection'):
                delattr(self, '_pre_drag_selection')
            
            # Emit selection changed signal
            self.selectionChanged.emit(list(self._selected_frames))
            self._update_selection_controls()
        
        super().mouseReleaseEvent(event)
    
    def _get_frame_at_position(self, position) -> Optional[int]:
        """Get the frame index at the given position."""
        # Find which thumbnail widget is at this position
        widget = self.childAt(position.toPoint())
        
        # Look for FrameThumbnail in the widget hierarchy
        while widget and not isinstance(widget, FrameThumbnail):
            widget = widget.parent()
        
        if isinstance(widget, FrameThumbnail):
            return widget.frame_index
        
        return None
    
    def _update_drag_selection(self, start_frame: int, end_frame: int):
        """Update selection during drag operation."""
        # For drag selection, we want to show the range being dragged
        # but preserve any existing selection outside this range
        start = min(start_frame, end_frame)
        end = max(start_frame, end_frame)
        
        # Start with pre-drag selection (should be initialized in _on_drag_started)
        if hasattr(self, '_pre_drag_selection'):
            self._selected_frames = self._pre_drag_selection.copy()
        else:
            # Fallback if something went wrong
            self._selected_frames.clear()
        
        # Add the current drag range
        for i in range(start, end + 1):
            if i < len(self._thumbnails):
                self._selected_frames.add(i)
        
        # Update visual display
        self._update_selection_display()