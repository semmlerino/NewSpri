"""
Qt-related mock fixtures for integration tests.
Prevents dialog timeouts and allows verification of dialog calls.
"""

import pytest
from unittest.mock import MagicMock, patch
from contextlib import contextmanager


class MockQMessageBox:
    """Mock QMessageBox that records calls and returns sensible defaults."""
    
    def __init__(self):
        self.calls = []
        self.next_return_value = None
    
    def _record_call(self, method, parent, title, text, buttons=None, default_button=None):
        """Record a dialog call."""
        self.calls.append({
            'method': method,
            'parent': parent,
            'title': title,
            'text': text,
            'buttons': buttons,
            'default_button': default_button
        })
    
    def information(self, parent, title, text, buttons=None, default_button=None):
        """Mock QMessageBox.information."""
        self._record_call('information', parent, title, text, buttons, default_button)
        return self.next_return_value or 0
    
    def warning(self, parent, title, text, buttons=None, default_button=None):
        """Mock QMessageBox.warning."""
        self._record_call('warning', parent, title, text, buttons, default_button)
        return self.next_return_value or 0
    
    def critical(self, parent, title, text, buttons=None, default_button=None):
        """Mock QMessageBox.critical."""
        self._record_call('critical', parent, title, text, buttons, default_button)
        return self.next_return_value or 0
    
    def question(self, parent, title, text, buttons=None, default_button=None):
        """Mock QMessageBox.question - returns Yes by default."""
        self._record_call('question', parent, title, text, buttons, default_button)
        # Return Yes button value (typically 16384 in Qt)
        return self.next_return_value or 16384
    
    def about(self, parent, title, text):
        """Mock QMessageBox.about."""
        self._record_call('about', parent, title, text)
    
    def aboutQt(self, parent, title=None):
        """Mock QMessageBox.aboutQt."""
        self._record_call('aboutQt', parent, title, None)
    
    def reset(self):
        """Reset recorded calls."""
        self.calls = []
        self.next_return_value = None
    
    def get_calls(self, method=None):
        """Get recorded calls, optionally filtered by method."""
        if method:
            return [c for c in self.calls if c['method'] == method]
        return self.calls
    
    def set_next_return(self, value):
        """Set the return value for the next dialog call."""
        self.next_return_value = value


@pytest.fixture
def mock_qmessagebox():
    """Fixture that provides a mock QMessageBox and patches it globally."""
    mock = MockQMessageBox()
    
    with patch('PySide6.QtWidgets.QMessageBox.information', mock.information), \
         patch('PySide6.QtWidgets.QMessageBox.warning', mock.warning), \
         patch('PySide6.QtWidgets.QMessageBox.critical', mock.critical), \
         patch('PySide6.QtWidgets.QMessageBox.question', mock.question), \
         patch('PySide6.QtWidgets.QMessageBox.about', mock.about), \
         patch('PySide6.QtWidgets.QMessageBox.aboutQt', mock.aboutQt):
        yield mock


@pytest.fixture(autouse=True)
def auto_mock_qmessagebox(request):
    """
    Automatically mock QMessageBox for all integration tests.
    This prevents timeout issues from modal dialogs.
    """
    # Only apply to integration tests
    if 'integration' in str(request.fspath):
        mock = MockQMessageBox()
        
        with patch('PySide6.QtWidgets.QMessageBox.information', mock.information), \
             patch('PySide6.QtWidgets.QMessageBox.warning', mock.warning), \
             patch('PySide6.QtWidgets.QMessageBox.critical', mock.critical), \
             patch('PySide6.QtWidgets.QMessageBox.question', mock.question), \
             patch('PySide6.QtWidgets.QMessageBox.about', mock.about), \
             patch('PySide6.QtWidgets.QMessageBox.aboutQt', mock.aboutQt):
            yield mock
    else:
        yield None


@contextmanager
def mock_qinputdialog(return_text="Test", return_ok=True):
    """Context manager to mock QInputDialog.getText."""
    with patch('PySide6.QtWidgets.QInputDialog.getText') as mock:
        mock.return_value = (return_text, return_ok)
        yield mock


@contextmanager
def mock_qfiledialog(return_path="/test/path", dialog_type="getOpenFileName"):
    """Context manager to mock QFileDialog methods."""
    with patch(f'PySide6.QtWidgets.QFileDialog.{dialog_type}') as mock:
        if dialog_type in ['getOpenFileName', 'getSaveFileName']:
            mock.return_value = (return_path, "")
        elif dialog_type == 'getExistingDirectory':
            mock.return_value = return_path
        elif dialog_type in ['getOpenFileNames']:
            mock.return_value = ([return_path], "")
        yield mock


# Re-export common Qt button values for tests
class QtButtons:
    """Common Qt button values for testing."""
    Ok = 1024
    Cancel = 4194304
    Yes = 16384
    No = 65536
    Save = 2048
    Discard = 8388608
    Apply = 33554432