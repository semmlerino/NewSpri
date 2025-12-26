"""
Custom widget components for export operations.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout


class ExportProgressDialog(QDialog):
    """Simple progress dialog for export operations."""

    cancelled = Signal()

    def __init__(self, export_type: str, total_frames: int, parent=None):
        super().__init__(parent)

        self.total_frames = total_frames
        self.current_frame = 0

        self.setWindowTitle("Exporting...")
        self.setModal(True)
        self.setFixedSize(400, 150)

        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Export type label
        self.type_label = QLabel(f"Exporting {export_type}")
        font = self.type_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.type_label.setFont(font)
        layout.addWidget(self.type_label)

        # Progress label
        self.progress_label = QLabel("Preparing export...")
        layout.addWidget(self.progress_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(total_frames)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress display."""
        self.current_frame = current
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

        if message:
            self.progress_label.setText(message)
        else:
            self.progress_label.setText(f"Processing frame {current} of {total}")

    def _on_cancel(self):
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()
