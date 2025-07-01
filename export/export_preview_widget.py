"""
Export Preview Widget
Shows live preview of export output including file names, sizes, and structure.
Part of Phase 1: Export Dialog Redesign implementation.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QGroupBox, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QPalette

from .export_presets import ExportPreset, get_preset_manager
from config import Config


class FilePreviewItem(QFrame):
    """Individual file preview item showing name, size, and type."""
    
    def __init__(self, filename: str, size_kb: float = 0.0, is_placeholder: bool = False):
        super().__init__()
        self.filename = filename
        self.size_kb = size_kb
        self.is_placeholder = is_placeholder
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the file preview item UI."""
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            FilePreviewItem {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # File icon based on extension
        icon_label = QLabel(self._get_file_icon())
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)
        
        # Filename
        filename_label = QLabel(self.filename)
        filename_font = QFont()
        filename_font.setPointSize(9)
        if self.is_placeholder:
            filename_font.setItalic(True)
            filename_label.setStyleSheet("color: #666;")
        filename_label.setFont(filename_font)
        layout.addWidget(filename_label, 1)
        
        # File size (if not placeholder)
        if not self.is_placeholder and self.size_kb > 0:
            size_text = self._format_file_size(self.size_kb)
            size_label = QLabel(size_text)
            size_label.setStyleSheet("color: #888; font-size: 8px;")
            size_label.setAlignment(Qt.AlignRight)
            layout.addWidget(size_label)
    
    def _get_file_icon(self) -> str:
        """Get appropriate emoji icon for file type."""
        ext = Path(self.filename).suffix.lower()
        
        if ext == '.png':
            return "🖼️"
        elif ext in ['.jpg', '.jpeg']:
            return "📷"
        elif ext == '.gif':
            return "🎬"
        elif ext == '.bmp':
            return "🖼️"
        else:
            return "📄"
    
    def _format_file_size(self, size_kb: float) -> str:
        """Format file size for display."""
        if size_kb < 1:
            return "< 1 KB"
        elif size_kb < 1024:
            return f"{size_kb:.0f} KB"
        else:
            return f"{size_kb/1024:.1f} MB"


class ExportSummaryWidget(QFrame):
    """Summary widget showing total files, size, and warnings."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the summary widget UI."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            ExportSummaryWidget {
                background-color: #e8f5e8;
                border: 1px solid #c8e6c9;
                border-radius: 6px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)
        
        # Summary text
        self.summary_label = QLabel()
        summary_font = QFont()
        summary_font.setPointSize(10)
        summary_font.setBold(True)
        self.summary_label.setFont(summary_font)
        layout.addWidget(self.summary_label, 1)
        
        # Warning/info icon
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
    
    def update_summary(self, file_count: int, total_size_mb: float, size_category: str):
        """Update the summary display."""
        # Format summary text
        if file_count == 1:
            files_text = "1 file"
        else:
            files_text = f"{file_count} files"
        
        if total_size_mb < 0.1:
            size_text = f"{total_size_mb * 1024:.0f} KB"
        else:
            size_text = f"{total_size_mb:.1f} MB"
        
        summary_text = f"📁 {files_text} • 💾 {size_text}"
        self.summary_label.setText(summary_text)
        
        # Set status icon and styling based on size
        if size_category in ["tiny", "small"]:
            self.status_label.setText("✅")
            self.setStyleSheet("""
                ExportSummaryWidget {
                    background-color: #e8f5e8;
                    border: 1px solid #c8e6c9;
                    border-radius: 6px;
                }
            """)
        elif size_category == "medium":
            self.status_label.setText("⚠️")
            self.setStyleSheet("""
                ExportSummaryWidget {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 6px;
                }
            """)
        elif size_category in ["large", "very_large"]:
            self.status_label.setText("🔴")
            self.setStyleSheet("""
                ExportSummaryWidget {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 6px;
                }
            """)


class ExportPreviewWidget(QGroupBox):
    """Complete export preview widget showing files and summary."""
    
    previewUpdated = Signal(dict)  # Emits preview data
    
    def __init__(self, parent=None):
        super().__init__("Preview", parent)
        self._current_preset: Optional[ExportPreset] = None
        self._frame_count = 0
        self._base_name = "frame"
        self._output_dir = ""
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the preview widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Description
        desc_label = QLabel("Files to be created:")
        desc_font = QFont()
        desc_font.setPointSize(10)
        desc_font.setBold(True)
        desc_label.setFont(desc_font)
        layout.addWidget(desc_label)
        
        # File list area
        self.file_scroll = QScrollArea()
        self.file_scroll.setMaximumHeight(120)
        self.file_scroll.setWidgetResizable(True)
        self.file_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.file_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.file_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        # File list container
        self.file_container = QWidget()
        self.file_layout = QVBoxLayout(self.file_container)
        self.file_layout.setContentsMargins(4, 4, 4, 4)
        self.file_layout.setSpacing(2)
        self.file_layout.addStretch()
        
        self.file_scroll.setWidget(self.file_container)
        layout.addWidget(self.file_scroll)
        
        # Summary
        self.summary_widget = ExportSummaryWidget()
        layout.addWidget(self.summary_widget)
        
        # Output location
        self.location_label = QLabel()
        self.location_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        self.location_label.setWordWrap(True)
        layout.addWidget(self.location_label)
        
        # Show placeholder initially
        self._show_placeholder()
    
    def update_preview(self, preset: ExportPreset, frame_count: int, 
                      base_name: str = "frame", output_dir: str = ""):
        """Update the preview based on current settings."""
        self._current_preset = preset
        self._frame_count = frame_count
        self._base_name = base_name or "frame"
        self._output_dir = output_dir
        
        if frame_count == 0:
            self._show_placeholder()
            return
        
        # Generate preview data
        preset_manager = get_preset_manager()
        preview_data = preset_manager.generate_output_preview(preset, frame_count, base_name)
        size_info = preset_manager.estimate_output_size(preset, frame_count)
        
        # Update file list
        self._update_file_list(preview_data['filenames'], size_info)
        
        # Update summary
        self.summary_widget.update_summary(
            preview_data['file_count'],
            preview_data['total_size_mb'],
            preview_data['size_category']
        )
        
        # Update location
        if output_dir:
            location_text = f"📁 Output: {output_dir}"
        else:
            location_text = "📁 Output: (select directory)"
        self.location_label.setText(location_text)
        
        # Emit preview data for other components
        full_preview_data = {
            **preview_data,
            **size_info,
            'preset': preset,
            'base_name': base_name,
            'output_dir': output_dir
        }
        self.previewUpdated.emit(full_preview_data)
    
    def _update_file_list(self, filenames: List[str], size_info: Dict[str, Any]):
        """Update the file list display."""
        # Clear existing items
        for i in reversed(range(self.file_layout.count())):
            child = self.file_layout.itemAt(i).widget()
            if child and isinstance(child, FilePreviewItem):
                child.setParent(None)
        
        # Add new file items
        avg_size_kb = size_info.get('avg_file_size_kb', 50.0)
        
        for filename in filenames:
            is_placeholder = filename.startswith("...")
            file_size = 0.0 if is_placeholder else avg_size_kb
            
            item = FilePreviewItem(filename, file_size, is_placeholder)
            self.file_layout.insertWidget(self.file_layout.count() - 1, item)
        
        # Add spacing if not many files
        if len(filenames) < 5:
            self.file_layout.addStretch()
    
    def _show_placeholder(self):
        """Show placeholder content when no frames are available."""
        # Clear file list
        for i in reversed(range(self.file_layout.count())):
            child = self.file_layout.itemAt(i).widget()
            if child and isinstance(child, FilePreviewItem):
                child.setParent(None)
        
        # Add placeholder
        placeholder = FilePreviewItem("No frames to export", 0.0, True)
        self.file_layout.insertWidget(0, placeholder)
        
        # Update summary
        self.summary_widget.update_summary(0, 0.0, "tiny")
        self.location_label.setText("📁 Load frames to see export preview")
    
    def get_current_preview_data(self) -> Optional[Dict[str, Any]]:
        """Get the current preview data."""
        if not self._current_preset or self._frame_count == 0:
            return None
        
        preset_manager = get_preset_manager()
        preview_data = preset_manager.generate_output_preview(
            self._current_preset, self._frame_count, self._base_name
        )
        size_info = preset_manager.estimate_output_size(self._current_preset, self._frame_count)
        
        return {
            **preview_data,
            **size_info,
            'preset': self._current_preset,
            'base_name': self._base_name,
            'output_dir': self._output_dir
        }
    
    def show_export_progress(self, current: int, total: int, current_file: str = ""):
        """Show export progress in the preview area."""
        # Could add a progress overlay or update the summary
        progress_text = f"Exporting: {current}/{total}"
        if current_file:
            progress_text += f" - {current_file}"
        
        # Temporarily update the description
        desc_label = self.findChild(QLabel)
        if desc_label:
            desc_label.setText(progress_text)
    
    def reset_to_preview_mode(self):
        """Reset from progress mode back to normal preview."""
        desc_label = self.findChild(QLabel)
        if desc_label:
            desc_label.setText("Files to be created:")


class SizeWarningWidget(QFrame):
    """Widget that shows warnings about file sizes and export duration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.hide()  # Hidden by default
    
    def _setup_ui(self):
        """Set up the warning widget UI."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            SizeWarningWidget {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Warning icon
        icon_label = QLabel("⚠️")
        layout.addWidget(icon_label)
        
        # Warning text
        self.warning_label = QLabel()
        warning_font = QFont()
        warning_font.setPointSize(9)
        self.warning_label.setFont(warning_font)
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label, 1)
    
    def check_and_show_warnings(self, preview_data: Dict[str, Any]):
        """Check preview data and show warnings if needed."""
        warnings = []
        
        file_count = preview_data.get('file_count', 0)
        total_size_mb = preview_data.get('total_size_mb', 0.0)
        size_category = preview_data.get('size_category', 'small')
        
        # Check for large file counts
        if file_count > 100:
            warnings.append(f"This will create {file_count} files, which may take time to export.")
        
        # Check for large file sizes
        if size_category == "large":
            warnings.append(f"Export size (~{total_size_mb:.1f} MB) is quite large.")
        elif size_category == "very_large":
            warnings.append(f"Export size (~{total_size_mb:.1f} MB) is very large and may take significant time.")
        
        # Check for GIF-specific warnings
        preset = preview_data.get('preset')
        if preset and preset.mode == "gif" and file_count > 50:
            warnings.append("Large GIF animations may not play smoothly in all viewers.")
        
        if warnings:
            self.warning_label.setText(" ".join(warnings))
            self.show()
        else:
            self.hide()


# Convenience function for creating complete preview section
def create_export_preview_section(parent=None) -> tuple[ExportPreviewWidget, SizeWarningWidget]:
    """Create both preview widget and warning widget."""
    preview = ExportPreviewWidget(parent)
    warning = SizeWarningWidget(parent)
    
    # Connect preview updates to warning checks
    preview.previewUpdated.connect(warning.check_and_show_warnings)
    
    return preview, warning