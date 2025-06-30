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
    QInputDialog, QMessageBox, QSplitter, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QMouseEvent, QContextMenuEvent

from config import Config
from styles import StyleManager


@dataclass
class AnimationSegment:
    """Represents a single animation segment with start/end frames."""
    name: str
    start_frame: int
    end_frame: int
    color: QColor = None
    
    def __post_init__(self):
        if self.color is None:
            # Default to a random color based on name hash
            hash_val = hash(self.name) % 360
            self.color = QColor.fromHsv(hash_val, 180, 200)
    
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
        elif self._segment_color:
            border_color = self._segment_color.name()
            border_width = "2px"
            background = "#FFFFFF"
        else:
            border_color = "#CCCCCC"
            border_width = "1px"
            background = "#FFFFFF"
        
        hover_style = ""
        if not self._selected and not self._highlighted:
            hover_style = """
            QLabel:hover {
                border-color: #2196F3;
                background-color: #F0F8FF;
            }
            """
        
        self.setStyleSheet(f"""
            QLabel {{
                border: {border_width} solid {border_color};
                background-color: {background};
                border-radius: 4px;
                margin: 2px;
            }}
            {hover_style}
        """)
    
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
        self._update_style()
    
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


class SegmentListWidget(QListWidget):
    """Widget for displaying and managing animation segments."""
    
    segmentSelected = Signal(str)  # segment_name
    segmentDeleted = Signal(str)   # segment_name
    segmentRenamed = Signal(str, str)  # old_name, new_name
    segmentDoubleClicked = Signal(str)  # segment_name (for preview)
    
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(200)
        self.setMinimumWidth(150)
        
        # Connect double-click for preview
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def add_segment(self, segment: AnimationSegment):
        """Add a segment to the list."""
        item = QListWidgetItem(f"{segment.name}\n({segment.frame_count} frames)")
        item.setData(Qt.UserRole, segment.name)
        
        # Color the item
        item.setBackground(segment.color.lighter(150))
        
        self.addItem(item)
    
    def remove_segment(self, segment_name: str):
        """Remove a segment from the list."""
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == segment_name:
                self.takeItem(i)
                break
    
    def update_segment(self, segment: AnimationSegment):
        """Update an existing segment in the list."""
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == segment.name:
                item.setText(f"{segment.name}\n({segment.frame_count} frames)")
                item.setBackground(segment.color.lighter(150))
                break
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Show context menu for segment management."""
        item = self.itemAt(event.pos())
        if item:
            menu = QMenu(self)
            
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            
            action = menu.exec(event.globalPos())
            segment_name = item.data(Qt.UserRole)
            
            if action == rename_action:
                new_name, ok = QInputDialog.getText(
                    self, "Rename Segment", "Enter new name:", text=segment_name
                )
                if ok and new_name.strip():
                    self.segmentRenamed.emit(segment_name, new_name.strip())
            elif action == delete_action:
                reply = QMessageBox.question(
                    self, "Delete Segment", 
                    f"Are you sure you want to delete '{segment_name}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.segmentDeleted.emit(segment_name)
    
    def _on_item_double_clicked(self, item):
        """Handle double-click on segment item for preview."""
        if item:
            segment_name = item.data(Qt.UserRole)
            if segment_name:
                self.segmentDoubleClicked.emit(segment_name)


class AnimationGridView(QWidget):
    """Main grid view widget for animation frame selection and splitting."""
    
    # Signals
    frameSelected = Signal(int)  # frame_index (for status updates)
    framePreviewRequested = Signal(int)  # frame_index (for double-click preview)
    selectionChanged = Signal(list)  # selected_frame_indices
    segmentCreated = Signal(AnimationSegment)  # new_segment
    segmentDeleted = Signal(str)  # segment_name
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
        layout = QHBoxLayout(self)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side: Grid view
        self._setup_grid_area(splitter)
        
        # Right side: Segment management
        self._setup_segment_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([800, 200])
    
    def _setup_grid_area(self, parent):
        """Set up the main grid area."""
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        
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
        
        grid_layout.addLayout(controls_layout)
        
        # Add selection instructions
        instructions = QLabel(
            "Selection modes: Click = select • Drag = range • Shift+Click = extend range • "
            "Ctrl/Alt+Click = multi-select • Double-Click = preview"
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
        grid_layout.addWidget(instructions)
        
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
        grid_layout.addWidget(self._scroll_area)
        
        parent.addWidget(grid_widget)
    
    def _setup_segment_panel(self, parent):
        """Set up the segment management panel."""
        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        
        # Title
        title = QLabel("Animation Segments")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        panel_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Click to select • Double-click to preview")
        instructions.setStyleSheet("""
            QLabel {
                font-size: 9px;
                color: #666;
                margin-bottom: 5px;
            }
        """)
        instructions.setWordWrap(True)
        panel_layout.addWidget(instructions)
        
        # Segment list
        self._segment_list = SegmentListWidget()
        panel_layout.addWidget(self._segment_list)
        
        # Panel buttons
        self._export_btn = QPushButton("Export Selected")
        self._export_btn.setEnabled(False)  # Disabled until segment selected
        self._export_btn.clicked.connect(self._export_selected_segment)
        panel_layout.addWidget(self._export_btn)
        
        parent.addWidget(panel_widget)
    
    def _connect_signals(self):
        """Connect internal signals."""
        self._segment_list.segmentSelected.connect(self._on_segment_selected)
        self._segment_list.segmentDeleted.connect(self._delete_segment)
        self._segment_list.segmentRenamed.connect(self._rename_segment)
        self._segment_list.segmentDoubleClicked.connect(self._on_segment_double_clicked)
        
        # Connect to selection changes to update export button
        self._segment_list.itemSelectionChanged.connect(self._on_segment_list_selection_changed)
    
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
    
    def _on_frame_right_clicked(self, frame_index: int, position: QPoint):
        """Handle frame thumbnail right-click."""
        menu = QMenu(self)
        
        # Add frame to selection if not already selected
        if frame_index not in self._selected_frames:
            self._clear_selection()
            self._select_frame(frame_index)
            self._update_selection_display()
        
        if self._selected_frames:
            create_action = menu.addAction(f"Create segment from selection ({len(self._selected_frames)} frames)")
            create_action.triggered.connect(self._create_segment_from_selection)
        
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
        
        # Get segment name from user
        name, ok = QInputDialog.getText(
            self, "Create Animation Segment", 
            f"Enter name for {description}:",
            text=f"Animation_{len(self._segments) + 1}"
        )
        
        if ok and name.strip():
            segment = AnimationSegment(name.strip(), start, end)
            self.add_segment(segment)
            self._clear_selection()
            
            self.segmentCreated.emit(segment)
    
    def add_segment(self, segment: AnimationSegment):
        """Add a new animation segment."""
        self._segments[segment.name] = segment
        self._segment_list.add_segment(segment)
        self._update_segment_visualization()
    
    def _delete_segment(self, segment_name: str):
        """Delete an animation segment."""
        if segment_name in self._segments:
            del self._segments[segment_name]
            self._segment_list.remove_segment(segment_name)
            self._update_segment_visualization()
            self.segmentDeleted.emit(segment_name)
    
    def _rename_segment(self, old_name: str, new_name: str):
        """Rename an animation segment."""
        if old_name in self._segments and new_name not in self._segments:
            segment = self._segments.pop(old_name)
            segment.name = new_name
            self._segments[new_name] = segment
            
            self._segment_list.remove_segment(old_name)
            self._segment_list.add_segment(segment)
    
    def _update_segment_visualization(self):
        """Update visual markers for all segments."""
        # Clear all segment markers
        for thumbnail in self._thumbnails:
            thumbnail.set_segment_markers()
        
        # Apply segment markers
        for segment in self._segments.values():
            for i in range(segment.start_frame, segment.end_frame + 1):
                if i < len(self._thumbnails):
                    is_start = (i == segment.start_frame)
                    is_end = (i == segment.end_frame)
                    self._thumbnails[i].set_segment_markers(is_start, is_end, segment.color)
    
    def _on_segment_selected(self, segment_name: str):
        """Handle segment selection from list."""
        if segment_name in self._segments:
            segment = self._segments[segment_name]
            self.segmentSelected.emit(segment)
    
    def _on_segment_double_clicked(self, segment_name: str):
        """Handle segment double-click for preview."""
        if segment_name in self._segments:
            segment = self._segments[segment_name]
            self.segmentPreviewRequested.emit(segment)
    
    def _on_segment_list_selection_changed(self):
        """Handle changes in segment list selection to update export button."""
        current_item = self._segment_list.currentItem()
        if current_item:
            segment_name = current_item.data(Qt.UserRole)
            if segment_name and segment_name in self._segments:
                segment = self._segments[segment_name]
                self._export_btn.setEnabled(True)
                self._export_btn.setText(f"Export '{segment.name}'")
            else:
                self._export_btn.setEnabled(False)
                self._export_btn.setText("Export Selected")
        else:
            self._export_btn.setEnabled(False)
            self._export_btn.setText("Export Selected")
    
    def _export_selected_segment(self):
        """Export the currently selected segment."""
        current_item = self._segment_list.currentItem()
        if current_item:
            segment_name = current_item.data(Qt.UserRole)
            if segment_name in self._segments:
                self.exportRequested.emit(self._segments[segment_name])
    
    def get_segments(self) -> List[AnimationSegment]:
        """Get all current animation segments."""
        return list(self._segments.values())
    
    def clear_segments(self):
        """Clear all animation segments."""
        self._segments.clear()
        self._segment_list.clear()
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