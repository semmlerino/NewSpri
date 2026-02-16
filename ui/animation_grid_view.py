"""
Animation Grid View - Frame selection and animation splitting component
Provides a grid view of all sprite frames with selection capabilities for animation splitting.
Part of Animation Splitting Feature implementation.
"""

import copy

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from config import Config
from managers import AnimationSegment
from utils.sprite_rendering import create_padded_pixmap
from utils.styles import StyleManager


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
        self._drag_threshold = Config.UI.DRAG_THRESHOLD

        # Set up the thumbnail
        self._setup_thumbnail(pixmap)
        self._update_style()

    def _setup_thumbnail(self, pixmap: QPixmap):
        """Set up the thumbnail display."""
        if pixmap and not pixmap.isNull():
            # Create padded pixmap to prevent edge cutoff
            padded = create_padded_pixmap(pixmap, padding=1)

            # Scale to fit available space
            padding = Config.UI.THUMBNAIL_PADDING
            available_size = self._thumbnail_size - padding
            scaled_pixmap = padded.scaled(
                available_size,
                available_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled_pixmap)

        border_space = Config.UI.THUMBNAIL_PADDING * 2
        self.setFixedSize(self._thumbnail_size + border_space, self._thumbnail_size + border_space)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setToolTip(f"Frame {self.frame_index}")

    def _update_style(self):
        """Update visual style based on selection state."""
        segment_color = None
        segment_bg = None
        if self._segment_color is not None and self._segment_color.isValid():
            segment_color = self._segment_color.name()
            segment_bg = self._segment_color.lighter(180).name()

        self.setStyleSheet(
            StyleManager.thumbnail_style(
                selected=self._selected,
                highlighted=self._highlighted,
                segment_color=segment_color,
                segment_bg=segment_bg,
                is_segment_start=self._is_segment_start,
                is_segment_end=self._is_segment_end,
            )
        )

    def set_selected(self, selected: bool):
        """Set selection state."""
        self._selected = selected
        self._update_style()

    def set_highlighted(self, highlighted: bool):
        """Set highlighted state (for drag-over effects)."""
        self._highlighted = highlighted
        self._update_style()

    def set_segment_markers(
        self, is_start: bool = False, is_end: bool = False, color: QColor | None = None
    ):
        """Set segment start/end markers."""
        self._is_segment_start = is_start
        self._is_segment_end = is_end
        self._segment_color = color

        # Update the visual style
        self._update_style()

        # Schedule visual update (Qt batches efficiently)
        self.update()

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

        # Schedule visual update (Qt batches efficiently)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events with modifier support."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_press_pos = event.position()
            # Convert modifiers to integer via .value attribute
            modifiers_value = event.modifiers().value
            self.clicked.emit(self.frame_index, modifiers_value)
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit(self.frame_index, event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click for frame preview."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit(self.frame_index)
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for drag detection."""
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._mouse_press_pos
            and (event.position() - self._mouse_press_pos).manhattanLength() > self._drag_threshold
        ):
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
    segmentRenamed = Signal(str, str)  # old_name, new_name (kept for compat)
    segmentRenameRequested = Signal(str, str)  # old_name, new_name (validate-first)
    segmentSelected = Signal(AnimationSegment)  # selected_segment
    segmentPreviewRequested = Signal(AnimationSegment)  # segment_to_preview (double-click)
    exportRequested = Signal(str)  # segment_name

    def __init__(self):
        super().__init__()

        # State
        self._frames: list[QPixmap] = []
        self._thumbnails: list[FrameThumbnail] = []
        self._segments: dict[str, AnimationSegment] = {}

        # Enhanced selection state
        self._selected_frames: set[int] = set()  # All selected frame indices
        self._last_clicked_frame: int | None = None  # For range selection
        self._drag_start_frame: int | None = None  # For drag selection
        self._is_dragging: bool = False
        self._pre_drag_selection: set[int] = set()  # Selection state before drag

        # UI settings
        self._grid_columns = 8
        self._thumbnail_size = Config.UI.THUMBNAIL_SIZE

        # Color assignment for segments
        self._segment_color_index = 0

        self._setup_ui()

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
        self._columns_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Grid container
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(2)

        self._scroll_area.setWidget(self._grid_container)
        parent_layout.addWidget(self._scroll_area)

    def set_frames(self, frames: list[QPixmap]):
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
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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
                self._clear_grid()
                self._populate_grid()

    def _on_frame_clicked(self, frame_index: int, modifiers: int):
        """Handle frame thumbnail click with keyboard modifiers."""
        from PySide6.QtCore import Qt

        # Check modifiers using bitwise operations directly on the integer value
        ctrl_pressed = bool(modifiers & int(Qt.KeyboardModifier.ControlModifier.value))
        alt_pressed = bool(modifiers & int(Qt.KeyboardModifier.AltModifier.value))
        shift_pressed = bool(modifiers & int(Qt.KeyboardModifier.ShiftModifier.value))

        if ctrl_pressed or alt_pressed:
            # Ctrl/Alt+Click: Toggle individual frame selection
            self._toggle_frame_selection(frame_index)
        elif shift_pressed and self._last_clicked_frame is not None:
            # Shift+Click: Range selection from last clicked frame
            self._select_frame_range(self._last_clicked_frame, frame_index)
        else:
            # Normal click: Clear previous selection and select this frame
            self._clear_selection()
            self._select_frame(frame_index)

        self._last_clicked_frame = frame_index
        self._update_selection_display()
        self._update_selection_controls()

        # Emit signal for status updates
        self.frameSelected.emit(frame_index)

        # Emit selection changed signal
        self.selectionChanged.emit(list(self._selected_frames))

    def _on_frame_double_clicked(self, frame_index: int):
        """Handle frame double-click for preview."""
        self.framePreviewRequested.emit(frame_index)

    def _on_drag_started(self, frame_index: int):
        """Handle start of drag selection."""
        self._drag_start_frame = frame_index
        self._is_dragging = True

        # If starting drag from unselected frame, clear and select it
        if frame_index not in self._selected_frames:
            self._selected_frames.clear()
            self._selected_frames.add(frame_index)

        # Store current selection state for drag extension
        self._pre_drag_selection = self._selected_frames.copy()
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

    def _get_segment_at_frame(self, frame_index: int) -> AnimationSegment | None:
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
            export_frames_action.triggered.connect(lambda: self.exportRequested.emit(segment.name))

            export_sheet_action = segment_menu.addAction("Export as Sprite Sheet...")
            export_sheet_action.triggered.connect(lambda: self.exportRequested.emit(segment.name))

            segment_menu.addSeparator()

            # Rename segment action
            rename_action = segment_menu.addAction("Rename Segment...")
            rename_action.triggered.connect(lambda: self._prompt_rename_segment(segment.name))

            # Delete segment action
            delete_action = segment_menu.addAction("Delete Segment")
            delete_action.triggered.connect(lambda: self.delete_segment(segment.name))

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
                action_text = (
                    f"Add frames {sorted_frames[0]}-{sorted_frames[-1]} as animation segment"
                )
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
                    self._create_segment_btn.setText(
                        f"Create Animation Segment (frames {start}-{end})"
                    )
                else:
                    self._create_segment_btn.setText(f"Create Animation Segment ({count} frames)")
        else:
            self._create_segment_btn.setText("Create Animation Segment")

    def _is_contiguous_selection(self, sorted_frames: list[int]) -> bool:
        """Check if the selected frames form a contiguous range."""
        if not sorted_frames:
            return False

        for i in range(1, len(sorted_frames)):
            if sorted_frames[i] != sorted_frames[i - 1] + 1:
                return False
        return True

    def _clear_selection(self):
        """Clear current selection."""
        self._selected_frames.clear()
        self._last_clicked_frame = None
        self._drag_start_frame = None
        self._is_dragging = False
        self._pre_drag_selection.clear()
        self._update_selection_display()
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
            total_frames = end - start + 1
            unselected_count = total_frames - len(sorted_frames)
            reply = QMessageBox.question(
                self,
                "Non-contiguous Selection",
                f"Your selection has gaps between frames.\n\n"
                f"Selected: frames {', '.join(str(f) for f in sorted_frames[:5])}"
                f"{'...' if len(sorted_frames) > 5 else ''}\n"
                f"Segment will span: frames {start} to {end} ({total_frames} total)\n"
                f"Includes {unselected_count} unselected frame(s) in between.\n\n"
                f"Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Generate unique default name
        default_name = self._generate_unique_segment_name()

        # Get segment name from user
        name, ok = QInputDialog.getText(
            self, "Create Animation Segment", f"Enter name for {description}:", text=default_name
        )

        if ok and name.strip():
            segment = AnimationSegment(
                name=name.strip(),
                start_frame=start,
                end_frame=end,
            )
            segment.set_color(self._get_next_segment_color())
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

    def _get_next_segment_color(self) -> QColor:
        """Get the next color for a new segment from the palette."""
        palette = Config.Colors.SEGMENT_PALETTE
        color_hex = palette[self._segment_color_index % len(palette)]
        self._segment_color_index += 1
        return QColor(color_hex)

    def add_segment(self, segment: AnimationSegment):
        """Add a new animation segment."""
        self._segments[segment.name] = segment
        self._update_segment_visualization()

    def sync_segments_with_manager(self, segment_manager):
        """Synchronize local segments with segment manager to prevent conflicts."""
        if not segment_manager:
            return

        # Get all segments from manager (now same type as grid uses)
        manager_segments = segment_manager.get_all_segments()

        # Clear current segments and rebuild from manager
        self._segments.clear()

        # Add copies of segments to ensure data independence
        for segment in manager_segments:
            self._segments[segment.name] = copy.deepcopy(segment)

        # Update visualization
        self._update_segment_visualization()

    def delete_segment(self, segment_name: str) -> bool:
        """Delete an animation segment by name.

        Args:
            segment_name: Name of segment to delete

        Returns:
            True if segment was deleted, False if not found
        """
        if segment_name in self._segments:
            del self._segments[segment_name]
            self._update_segment_visualization()
            self.segmentDeleted.emit(segment_name)
            return True
        return False

    def _prompt_rename_segment(self, old_name: str):
        """Prompt user to rename a segment (validate-first: emits request, doesn't mutate)."""
        new_name, ok = QInputDialog.getText(
            self, "Rename Segment", f"Enter new name for '{old_name}':", text=old_name
        )

        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name != old_name:
                # Emit request — controller validates via manager, then calls commit_rename
                self.segmentRenameRequested.emit(old_name, new_name)

    def commit_rename(self, old_name: str, new_name: str) -> bool:
        """Commit a validated rename to local grid state.

        Called by controller after manager validation succeeds.

        Args:
            old_name: Current name of segment
            new_name: New name for segment

        Returns:
            True if renamed successfully
        """
        if old_name in self._segments and new_name not in self._segments:
            segment = self._segments.pop(old_name)
            segment.name = new_name
            self._segments[new_name] = segment
            self._update_segment_visualization()
            self.segmentRenamed.emit(old_name, new_name)
            return True
        return False

    # ============================================================================
    # PUBLIC SEGMENT MANIPULATION API
    # ============================================================================

    def rename_segment(self, old_name: str, new_name: str) -> bool:
        """Rename an animation segment.

        Args:
            old_name: Current name of segment
            new_name: New name for segment

        Returns:
            True if renamed successfully, False if old_name not found or new_name exists
        """
        if old_name in self._segments and new_name not in self._segments:
            segment = self._segments.pop(old_name)
            segment.name = new_name
            self._segments[new_name] = segment
            self._update_segment_visualization()
            return True
        return False

    def has_segment(self, segment_name: str) -> bool:
        """
        Check if a segment with the given name exists.

        Args:
            segment_name: Name to check

        Returns:
            True if segment exists, False otherwise
        """
        return segment_name in self._segments

    def _update_segment_visualization(self):
        """Update visual markers for all segments."""
        # Clear all thumbnails to default state
        for thumbnail in self._thumbnails:
            thumbnail.force_clear_style()

        # Apply segment markers
        for segment in self._segments.values():
            for i in range(segment.start_frame, segment.end_frame + 1):
                if i < len(self._thumbnails):
                    is_start = i == segment.start_frame
                    is_end = i == segment.end_frame
                    self._thumbnails[i].set_segment_markers(is_start, is_end, segment.color)

        # Single update call is sufficient - Qt will batch repaints
        self.update()

    def _preview_selection(self):
        """Preview the currently selected frames as an animation."""
        if not self._selected_frames or not self._frames:
            return

        sorted_frames = sorted(self._selected_frames)
        # Create temporary segment for preview with default color
        temp_segment = AnimationSegment(
            name="Preview",
            start_frame=sorted_frames[0],
            end_frame=sorted_frames[-1],
        )
        temp_segment.set_color(QColor(Config.Colors.SEGMENT_PALETTE[0]))
        self.segmentPreviewRequested.emit(temp_segment)

    def get_segments(self) -> list[AnimationSegment]:
        """Get all current animation segments."""
        return list(self._segments.values())

    def clear_segments(self):
        """Clear all animation segments."""
        self._segments.clear()
        # Reset color index for fresh color sequence
        self._segment_color_index = 0
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
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self._drag_start_frame = None
            self._pre_drag_selection.clear()
            self.selectionChanged.emit(list(self._selected_frames))
            self._update_selection_controls()

        super().mouseReleaseEvent(event)

    def _get_frame_at_position(self, position) -> int | None:
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
        start = min(start_frame, end_frame)
        end = max(start_frame, end_frame)

        # Start with pre-drag selection and add drag range
        self._selected_frames = self._pre_drag_selection.copy()
        self._selected_frames.update(range(start, min(end + 1, len(self._thumbnails))))
        self._update_selection_display()
