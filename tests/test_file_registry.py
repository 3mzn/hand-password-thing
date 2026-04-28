"""
Unit tests for the file registry module.
"""

import json
import os
import tempfile
import pytest
from pathlib import Path

from src.file_registry import EncryptedFileEntry, FileRegistry


class TestEncryptedFileEntry:
    """Tests for EncryptedFileEntry dataclass."""
    
    def test_create_entry_with_uuid(self):
        """Test creating an entry generates a valid UUID."""
        entry = EncryptedFileEntry.create(
            original_path="/path/to/file.txt",
            encrypted_path="/path/to/file.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file.txt"
        )
        
        assert entry.file_id is not None
        assert len(entry.file_id) == 36  # UUID format
        assert entry.original_path == "/path/to/file.txt"
        assert entry.encrypted_path == "/path/to/file.txt.enc"
        assert entry.gesture_password == [1, 2, 3, 4, 5]
        assert entry.file_name == "file.txt"
    
    def test_create_entry_unique_ids(self):
        """Test that multiple entries get unique IDs."""
        entry1 = EncryptedFileEntry.create(
            original_path="/path/to/file1.txt",
            encrypted_path="/path/to/file1.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file1.txt"
        )
        
        entry2 = EncryptedFileEntry.create(
            original_path="/path/to/file2.txt",
            encrypted_path="/path/to/file2.txt.enc",
            gesture_password=[5, 4, 3, 2, 1],
            file_name="file2.txt"
        )
        
        assert entry1.file_id != entry2.file_id


class TestFileRegistry:
    """Tests for FileRegistry class."""
    
    @pytest.fixture
    def temp_registry_file(self):
        """Create a temporary registry file for testing."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_init_creates_empty_registry(self, temp_registry_file):
        """Test initializing a new registry."""
        registry = FileRegistry(temp_registry_file)
        assert registry.registry_path == temp_registry_file
        assert len(registry.entries) == 0
    
    def test_add_entry(self, temp_registry_file):
        """Test adding an entry to the registry."""
        registry = FileRegistry(temp_registry_file)
        entry = EncryptedFileEntry.create(
            original_path="/path/to/file.txt",
            encrypted_path="/path/to/file.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file.txt"
        )
        
        registry.add_entry(entry)
        
        assert len(registry.entries) == 1
        assert entry.file_id in registry.entries
        assert registry.entries[entry.file_id] == entry
    
    def test_remove_entry(self, temp_registry_file):
        """Test removing an entry from the registry."""
        registry = FileRegistry(temp_registry_file)
        entry = EncryptedFileEntry.create(
            original_path="/path/to/file.txt",
            encrypted_path="/path/to/file.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file.txt"
        )
        
        registry.add_entry(entry)
        assert len(registry.entries) == 1
        
        registry.remove_entry(entry.file_id)
        assert len(registry.entries) == 0
        assert entry.file_id not in registry.entries
    
    def test_remove_nonexistent_entry(self, temp_registry_file):
        """Test removing a non-existent entry doesn't raise an error."""
        registry = FileRegistry(temp_registry_file)
        registry.remove_entry("nonexistent-id")
        assert len(registry.entries) == 0
    
    def test_get_entry(self, temp_registry_file):
        """Test retrieving an entry by file ID."""
        registry = FileRegistry(temp_registry_file)
        entry = EncryptedFileEntry.create(
            original_path="/path/to/file.txt",
            encrypted_path="/path/to/file.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file.txt"
        )
        
        registry.add_entry(entry)
        
        retrieved = registry.get_entry(entry.file_id)
        assert retrieved is not None
        assert retrieved == entry
    
    def test_get_nonexistent_entry(self, temp_registry_file):
        """Test retrieving a non-existent entry returns None."""
        registry = FileRegistry(temp_registry_file)
        retrieved = registry.get_entry("nonexistent-id")
        assert retrieved is None
    
    def test_list_entries(self, temp_registry_file):
        """Test listing all entries."""
        registry = FileRegistry(temp_registry_file)
        
        entry1 = EncryptedFileEntry.create(
            original_path="/path/to/file1.txt",
            encrypted_path="/path/to/file1.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file1.txt"
        )
        
        entry2 = EncryptedFileEntry.create(
            original_path="/path/to/file2.txt",
            encrypted_path="/path/to/file2.txt.enc",
            gesture_password=[5, 4, 3, 2, 1],
            file_name="file2.txt"
        )
        
        registry.add_entry(entry1)
        registry.add_entry(entry2)
        
        entries = registry.list_entries()
        assert len(entries) == 2
        assert entry1 in entries
        assert entry2 in entries
    
    def test_save_and_load(self, temp_registry_file):
        """Test saving and loading the registry."""
        # Create and populate registry
        registry = FileRegistry(temp_registry_file)
        entry1 = EncryptedFileEntry.create(
            original_path="/path/to/file1.txt",
            encrypted_path="/path/to/file1.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file1.txt"
        )
        entry2 = EncryptedFileEntry.create(
            original_path="/path/to/file2.txt",
            encrypted_path="/path/to/file2.txt.enc",
            gesture_password=[5, 4, 3, 2, 1],
            file_name="file2.txt"
        )
        
        registry.add_entry(entry1)
        registry.add_entry(entry2)
        registry.save()
        
        # Load registry from file
        loaded_registry = FileRegistry.load(temp_registry_file)
        
        assert len(loaded_registry.entries) == 2
        assert entry1.file_id in loaded_registry.entries
        assert entry2.file_id in loaded_registry.entries
        
        loaded_entry1 = loaded_registry.get_entry(entry1.file_id)
        assert loaded_entry1.original_path == entry1.original_path
        assert loaded_entry1.encrypted_path == entry1.encrypted_path
        assert loaded_entry1.gesture_password == entry1.gesture_password
        assert loaded_entry1.file_name == entry1.file_name
    
    def test_load_from_nonexistent_file(self, temp_registry_file):
        """Test loading from a non-existent file creates empty registry."""
        # Remove the temp file
        os.unlink(temp_registry_file)
        
        registry = FileRegistry.load(temp_registry_file)
        
        assert len(registry.entries) == 0
        assert registry.registry_path == temp_registry_file
    
    def test_load_from_corrupted_file(self, temp_registry_file):
        """Test loading from a corrupted file creates empty registry."""
        # Write invalid JSON
        with open(temp_registry_file, 'w') as f:
            f.write("{ invalid json }")
        
        registry = FileRegistry.load(temp_registry_file)
        
        assert len(registry.entries) == 0
    
    def test_save_creates_valid_json(self, temp_registry_file):
        """Test that save creates valid JSON with correct structure."""
        registry = FileRegistry(temp_registry_file)
        entry = EncryptedFileEntry.create(
            original_path="/path/to/file.txt",
            encrypted_path="/path/to/file.txt.enc",
            gesture_password=[1, 2, 3, 4, 5],
            file_name="file.txt"
        )
        
        registry.add_entry(entry)
        registry.save()
        
        # Read and verify JSON structure
        with open(temp_registry_file, 'r') as f:
            data = json.load(f)
        
        assert 'entries' in data
        assert len(data['entries']) == 1
        assert data['entries'][0]['file_id'] == entry.file_id
        assert data['entries'][0]['original_path'] == entry.original_path
        assert data['entries'][0]['encrypted_path'] == entry.encrypted_path
        assert data['entries'][0]['gesture_password'] == entry.gesture_password
        assert data['entries'][0]['file_name'] == entry.file_name
