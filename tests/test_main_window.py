"""
Tests for MainWindow encryption workflow integration.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

from src.main_window import MainWindow
from src.file_registry import FileRegistry
from src.file_encryption_manager import FileEncryptionManager
from src.gesture_capture import GestureCapture


class TestMainWindowEncryptionWorkflow(unittest.TestCase):
    """Test the encryption workflow wiring in MainWindow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.temp_dir, "test_registry.json")
        self.registry = FileRegistry(self.registry_path)
        
        # Mock the Tkinter root to avoid GUI creation
        with patch('tkinter.Tk'):
            self.window = MainWindow(self.registry)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_handle_add_file_with_callback(self):
        """Test that _handle_add_file calls the callback if set."""
        mock_callback = Mock()
        self.window.on_add_file = mock_callback
        
        self.window._handle_add_file()
        
        mock_callback.assert_called_once()
    
    def test_handle_decrypt_file_with_callback(self):
        """Test that _handle_decrypt_file calls the callback if set."""
        mock_callback = Mock()
        self.window.on_decrypt_file = mock_callback
        
        self.window._handle_decrypt_file("test-file-id")
        
        mock_callback.assert_called_once_with("test-file-id")
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_add_file_workflow_success(self, mock_fem_class, mock_gc_class):
        """Test the default add file workflow with successful encryption."""
        # Setup mocks
        mock_fem = Mock()
        mock_fem.encrypt_file.return_value = (True, "test-file-id")
        mock_fem_class.return_value = mock_fem
        
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = [0, 1, 2, 3, 4]
        mock_gc_class.return_value = mock_gc
        
        # Mock the dialog and message boxes
        with patch.object(self.window, 'show_file_dialog', return_value='/path/to/file.txt'):
            with patch.object(self.window, 'show_success') as mock_success:
                with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                    self.window._default_add_file_workflow()
        
        # Verify the workflow
        mock_gc.capture_gesture_password.assert_called_once_with("enroll")
        mock_fem.encrypt_file.assert_called_once_with('/path/to/file.txt', [0, 1, 2, 3, 4])
        mock_success.assert_called_once()
        mock_refresh.assert_called_once()
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_add_file_workflow_cancelled_dialog(self, mock_fem_class, mock_gc_class):
        """Test workflow when user cancels file dialog."""
        with patch.object(self.window, 'show_file_dialog', return_value=None):
            self.window._default_add_file_workflow()
        
        # Gesture capture should not be called
        mock_gc_class.assert_not_called()
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_add_file_workflow_cancelled_gesture(self, mock_fem_class, mock_gc_class):
        """Test workflow when user cancels gesture capture."""
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = None
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_file_dialog', return_value='/path/to/file.txt'):
            with patch.object(self.window, 'show_info') as mock_info:
                self.window._default_add_file_workflow()
        
        # Encryption should not be called
        mock_fem_class.return_value.encrypt_file.assert_not_called()
        mock_info.assert_called_once_with("Gesture capture cancelled")
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_add_file_workflow_encryption_failure(self, mock_fem_class, mock_gc_class):
        """Test workflow when encryption fails."""
        mock_fem = Mock()
        mock_fem.encrypt_file.return_value = (False, "File too large")
        mock_fem_class.return_value = mock_fem
        
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = [0, 1, 2, 3, 4]
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_file_dialog', return_value='/path/to/file.txt'):
            with patch.object(self.window, 'show_error') as mock_error:
                with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                    self.window._default_add_file_workflow()
        
        # Error should be shown, but list should not refresh
        mock_error.assert_called_once_with("Encryption failed: File too large")
        mock_refresh.assert_not_called()
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_decrypt_file_workflow_success(self, mock_fem_class, mock_gc_class):
        """Test the default decrypt file workflow with successful decryption."""
        # Setup mocks
        mock_fem = Mock()
        mock_fem.decrypt_file.return_value = (True, "File decrypted successfully")
        mock_fem_class.return_value = mock_fem
        
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = [0, 1, 2, 3, 4]
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_success') as mock_success:
            with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                self.window._default_decrypt_file_workflow("test-file-id")
        
        # Verify the workflow
        mock_gc.capture_gesture_password.assert_called_once_with("verify")
        mock_fem.decrypt_file.assert_called_once_with("test-file-id", [0, 1, 2, 3, 4])
        mock_success.assert_called_once_with("File decrypted successfully")
        mock_refresh.assert_called_once()
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_decrypt_file_workflow_cancelled_gesture(self, mock_fem_class, mock_gc_class):
        """Test decrypt workflow when user cancels gesture capture."""
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = None
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_info') as mock_info:
            self.window._default_decrypt_file_workflow("test-file-id")
        
        # Decryption should not be called
        mock_fem_class.return_value.decrypt_file.assert_not_called()
        mock_info.assert_called_once_with("Gesture verification cancelled")
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_decrypt_file_workflow_access_denied(self, mock_fem_class, mock_gc_class):
        """Test decrypt workflow when wrong password is entered."""
        mock_fem = Mock()
        mock_fem.decrypt_file.return_value = (False, "Access Denied")
        mock_fem_class.return_value = mock_fem
        
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = [0, 1, 2, 3, 4]
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_error') as mock_error:
            with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                self.window._default_decrypt_file_workflow("test-file-id")
        
        # Error should be shown, but list should not refresh
        mock_error.assert_called_once_with("Access Denied: Incorrect gesture password")
        mock_refresh.assert_not_called()
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_decrypt_file_workflow_missing_file(self, mock_fem_class, mock_gc_class):
        """Test decrypt workflow when encrypted file is missing."""
        mock_fem = Mock()
        mock_fem.decrypt_file.return_value = (False, "Encrypted file not found on disk")
        mock_fem_class.return_value = mock_fem
        
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = [0, 1, 2, 3, 4]
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_error') as mock_error:
            with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                self.window._default_decrypt_file_workflow("test-file-id")
        
        # Error should be shown and list should refresh (file removed from registry)
        mock_error.assert_called_once_with("Encrypted file not found on disk. Removed from list.")
        mock_refresh.assert_called_once()
    
    @patch('src.gesture_capture.GestureCapture')
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_decrypt_file_workflow_other_error(self, mock_fem_class, mock_gc_class):
        """Test decrypt workflow with other decryption errors."""
        mock_fem = Mock()
        mock_fem.decrypt_file.return_value = (False, "Decryption failed: Invalid data")
        mock_fem_class.return_value = mock_fem
        
        mock_gc = Mock()
        mock_gc.capture_gesture_password.return_value = [0, 1, 2, 3, 4]
        mock_gc_class.return_value = mock_gc
        
        with patch.object(self.window, 'show_error') as mock_error:
            with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                self.window._default_decrypt_file_workflow("test-file-id")
        
        # Error should be shown, but list should not refresh
        mock_error.assert_called_once_with("Decryption failed: Decryption failed: Invalid data")
        mock_refresh.assert_not_called()
    
    def test_handle_remove_file_with_callback(self):
        """Test that _handle_remove_file calls the callback if set."""
        mock_callback = Mock()
        self.window.on_remove_file = mock_callback
        
        self.window._handle_remove_file("test-file-id")
        
        mock_callback.assert_called_once_with("test-file-id")
    
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_remove_file_workflow_delete_file(self, mock_fem_class):
        """Test the default remove file workflow when user chooses to delete file."""
        # Setup mocks
        mock_fem = Mock()
        mock_fem.remove_file.return_value = (True, "File removed successfully")
        mock_fem_class.return_value = mock_fem
        
        with patch.object(self.window, 'ask_delete_confirmation', return_value=True):
            with patch.object(self.window, 'show_success') as mock_success:
                with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                    self.window._default_remove_file_workflow("test-file-id")
        
        # Verify the workflow
        mock_fem.remove_file.assert_called_once_with("test-file-id", True)
        mock_success.assert_called_once_with("File deleted and removed from list")
        mock_refresh.assert_called_once()
    
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_remove_file_workflow_remove_from_list_only(self, mock_fem_class):
        """Test the default remove file workflow when user chooses to remove from list only."""
        # Setup mocks
        mock_fem = Mock()
        mock_fem.remove_file.return_value = (True, "File removed successfully")
        mock_fem_class.return_value = mock_fem
        
        with patch.object(self.window, 'ask_delete_confirmation', return_value=False):
            with patch.object(self.window, 'show_success') as mock_success:
                with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                    self.window._default_remove_file_workflow("test-file-id")
        
        # Verify the workflow
        mock_fem.remove_file.assert_called_once_with("test-file-id", False)
        mock_success.assert_called_once_with("File removed from list (encrypted file kept)")
        mock_refresh.assert_called_once()
    
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_remove_file_workflow_cancelled(self, mock_fem_class):
        """Test the default remove file workflow when user cancels."""
        mock_fem = Mock()
        mock_fem_class.return_value = mock_fem
        
        with patch.object(self.window, 'ask_delete_confirmation', return_value=None):
            self.window._default_remove_file_workflow("test-file-id")
        
        # Removal should not be called
        mock_fem.remove_file.assert_not_called()
    
    @patch('src.file_encryption_manager.FileEncryptionManager')
    def test_default_remove_file_workflow_failure(self, mock_fem_class):
        """Test the default remove file workflow when removal fails."""
        # Setup mocks
        mock_fem = Mock()
        mock_fem.remove_file.return_value = (False, "File not found in registry")
        mock_fem_class.return_value = mock_fem
        
        with patch.object(self.window, 'ask_delete_confirmation', return_value=True):
            with patch.object(self.window, 'show_error') as mock_error:
                with patch.object(self.window, 'refresh_file_list') as mock_refresh:
                    self.window._default_remove_file_workflow("test-file-id")
        
        # Error should be shown, but list should not refresh
        mock_error.assert_called_once_with("Removal failed: File not found in registry")
        mock_refresh.assert_not_called()


if __name__ == '__main__':
    unittest.main()
