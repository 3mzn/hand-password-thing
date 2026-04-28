"""
Unit tests for the FileEncryptionManager class.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.file_encryption_manager import FileEncryptionManager
from src.file_registry import FileRegistry


class TestFileEncryptionManager:
    """Tests for FileEncryptionManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def temp_registry_file(self, temp_dir):
        """Create a temporary registry file path."""
        return os.path.join(temp_dir, "test_registry.json")
    
    @pytest.fixture
    def manager(self, temp_registry_file, monkeypatch):
        """Create a FileEncryptionManager with temporary registry."""
        # Patch the registry file location
        monkeypatch.setattr("src.file_registry.REGISTRY_FILE", temp_registry_file)
        monkeypatch.setattr("src.file_encryption_manager.FileRegistry.load", 
                           lambda: FileRegistry(temp_registry_file))
        
        manager = FileEncryptionManager()
        manager.registry = FileRegistry(temp_registry_file)
        return manager
    
    @pytest.fixture
    def test_file(self, temp_dir):
        """Create a test file with some content."""
        file_path = os.path.join(temp_dir, "test_file.txt")
        with open(file_path, 'w') as f:
            f.write("This is test content for encryption.")
        return file_path
    
    def test_init(self, manager):
        """Test FileEncryptionManager initialization."""
        assert manager.encryption is not None
        assert manager.registry is not None
        assert manager.validator is not None
    
    def test_encrypt_file_success(self, manager, test_file):
        """Test successful file encryption."""
        gesture_password = [1, 2, 3, 4, 5]
        
        success, result = manager.encrypt_file(test_file, gesture_password)
        
        assert success is True
        assert result is not None  # Should return file_id
        
        # Verify encrypted file exists
        encrypted_path = test_file + '.enc'
        assert os.path.exists(encrypted_path)
        
        # Verify registry entry was created
        entry = manager.registry.get_entry(result)
        assert entry is not None
        assert entry.original_path == test_file
        assert entry.encrypted_path == encrypted_path
        assert entry.gesture_password == gesture_password
        assert entry.file_name == "test_file.txt"
    
    def test_encrypt_nonexistent_file(self, manager, temp_dir):
        """Test encrypting a non-existent file."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.txt")
        gesture_password = [1, 2, 3, 4, 5]
        
        success, message = manager.encrypt_file(nonexistent_file, gesture_password)
        
        assert success is False
        assert "does not exist" in message.lower()
    
    def test_encrypt_file_too_large(self, manager, temp_dir, monkeypatch):
        """Test encrypting a file that exceeds size limit."""
        # Create a file
        large_file = os.path.join(temp_dir, "large_file.txt")
        with open(large_file, 'w') as f:
            f.write("test")
        
        # Mock the file size check to simulate a large file
        def mock_validate_size(file_path, max_size):
            return False, "File size exceeds maximum limit of 100MB"
        
        monkeypatch.setattr(manager.validator, "validate_file_size", mock_validate_size)
        
        gesture_password = [1, 2, 3, 4, 5]
        success, message = manager.encrypt_file(large_file, gesture_password)
        
        assert success is False
        assert "exceeds maximum limit" in message
    
    def test_decrypt_file_success(self, manager, test_file):
        """Test successful file decryption."""
        gesture_password = [1, 2, 3, 4, 5]
        
        # First encrypt the file
        success, file_id = manager.encrypt_file(test_file, gesture_password)
        assert success is True
        
        # Delete the original file to simulate real scenario
        os.remove(test_file)
        assert not os.path.exists(test_file)
        
        # Now decrypt it
        success, message = manager.decrypt_file(file_id, gesture_password)
        
        assert success is True
        assert message == "File decrypted successfully"
        
        # Verify original file is restored
        assert os.path.exists(test_file)
        
        # Verify encrypted file is deleted
        encrypted_path = test_file + '.enc'
        assert not os.path.exists(encrypted_path)
        
        # Verify registry entry is removed
        entry = manager.registry.get_entry(file_id)
        assert entry is None
    
    def test_decrypt_file_wrong_password(self, manager, test_file):
        """Test decryption with incorrect gesture password."""
        correct_password = [1, 2, 3, 4, 5]
        wrong_password = [5, 4, 3, 2, 1]
        
        # Encrypt the file
        success, file_id = manager.encrypt_file(test_file, correct_password)
        assert success is True
        
        # Try to decrypt with wrong password
        success, message = manager.decrypt_file(file_id, wrong_password)
        
        assert success is False
        assert message == "Access Denied"
        
        # Verify encrypted file still exists
        encrypted_path = test_file + '.enc'
        assert os.path.exists(encrypted_path)
        
        # Verify registry entry still exists
        entry = manager.registry.get_entry(file_id)
        assert entry is not None
    
    def test_decrypt_nonexistent_file_id(self, manager):
        """Test decrypting with a non-existent file ID."""
        gesture_password = [1, 2, 3, 4, 5]
        
        success, message = manager.decrypt_file("nonexistent-id", gesture_password)
        
        assert success is False
        assert "not found in registry" in message.lower()
    
    def test_decrypt_missing_encrypted_file(self, manager, test_file):
        """Test decryption when encrypted file is missing from disk."""
        gesture_password = [1, 2, 3, 4, 5]
        
        # Encrypt the file
        success, file_id = manager.encrypt_file(test_file, gesture_password)
        assert success is True
        
        # Delete the encrypted file to simulate missing file
        encrypted_path = test_file + '.enc'
        os.remove(encrypted_path)
        
        # Try to decrypt
        success, message = manager.decrypt_file(file_id, gesture_password)
        
        assert success is False
        assert "not found on disk" in message.lower()
        
        # Verify registry entry was removed
        entry = manager.registry.get_entry(file_id)
        assert entry is None
    
    def test_remove_file_with_deletion(self, manager, test_file):
        """Test removing a file with encrypted file deletion."""
        gesture_password = [1, 2, 3, 4, 5]
        
        # Encrypt the file
        success, file_id = manager.encrypt_file(test_file, gesture_password)
        assert success is True
        
        encrypted_path = test_file + '.enc'
        assert os.path.exists(encrypted_path)
        
        # Remove with deletion
        success, message = manager.remove_file(file_id, delete_encrypted=True)
        
        assert success is True
        assert message == "File removed successfully"
        
        # Verify encrypted file is deleted
        assert not os.path.exists(encrypted_path)
        
        # Verify registry entry is removed
        entry = manager.registry.get_entry(file_id)
        assert entry is None
    
    def test_remove_file_without_deletion(self, manager, test_file):
        """Test removing a file without deleting encrypted file."""
        gesture_password = [1, 2, 3, 4, 5]
        
        # Encrypt the file
        success, file_id = manager.encrypt_file(test_file, gesture_password)
        assert success is True
        
        encrypted_path = test_file + '.enc'
        assert os.path.exists(encrypted_path)
        
        # Remove without deletion
        success, message = manager.remove_file(file_id, delete_encrypted=False)
        
        assert success is True
        assert message == "File removed successfully"
        
        # Verify encrypted file still exists
        assert os.path.exists(encrypted_path)
        
        # Verify registry entry is removed
        entry = manager.registry.get_entry(file_id)
        assert entry is None
    
    def test_remove_nonexistent_file(self, manager):
        """Test removing a non-existent file."""
        success, message = manager.remove_file("nonexistent-id", delete_encrypted=True)
        
        assert success is False
        assert "not found in registry" in message.lower()
    
    def test_verify_encrypted_file_exists(self, manager, test_file):
        """Test verifying encrypted file existence."""
        gesture_password = [1, 2, 3, 4, 5]
        
        # Encrypt the file
        success, file_id = manager.encrypt_file(test_file, gesture_password)
        assert success is True
        
        # Verify it exists
        exists = manager.verify_encrypted_file_exists(file_id)
        assert exists is True
        
        # Delete the encrypted file
        encrypted_path = test_file + '.enc'
        os.remove(encrypted_path)
        
        # Verify it doesn't exist
        exists = manager.verify_encrypted_file_exists(file_id)
        assert exists is False
    
    def test_verify_nonexistent_file_id(self, manager):
        """Test verifying a non-existent file ID."""
        exists = manager.verify_encrypted_file_exists("nonexistent-id")
        assert exists is False
