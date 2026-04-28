"""
File registry module for managing encrypted file metadata.

This module provides the FileRegistry class for tracking encrypted files
and their associated metadata including gesture passwords.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from src.config import REGISTRY_FILE


@dataclass
class EncryptedFileEntry:
    """Represents metadata for a single encrypted file.
    
    Attributes:
        file_id: Unique identifier for the encrypted file (UUID)
        original_path: Path where the unencrypted file was located
        encrypted_path: Path where the encrypted file is stored
        gesture_password: List of gesture integers (plaintext)
        file_name: Name of the original file
    """
    file_id: str
    original_path: str
    encrypted_path: str
    gesture_password: list[int]
    file_name: str

    @staticmethod
    def create(original_path: str, encrypted_path: str, 
               gesture_password: list[int], file_name: str) -> "EncryptedFileEntry":
        """Create a new entry with a generated UUID."""
        return EncryptedFileEntry(
            file_id=str(uuid.uuid4()),
            original_path=original_path,
            encrypted_path=encrypted_path,
            gesture_password=gesture_password,
            file_name=file_name
        )


class FileRegistry:
    """Manages the registry of encrypted files stored in encrypted_files.json.
    
    The registry persists metadata for all encrypted files including their
    gesture passwords in plaintext format.
    """
    
    def __init__(self, registry_path: str = REGISTRY_FILE):
        """Initialize the file registry.
        
        Args:
            registry_path: Path to the registry JSON file
        """
        self.registry_path = registry_path
        self.entries: dict[str, EncryptedFileEntry] = {}
    
    @classmethod
    def load(cls, registry_path: str = REGISTRY_FILE) -> "FileRegistry":
        """Load the registry from encrypted_files.json.
        
        Args:
            registry_path: Path to the registry JSON file
            
        Returns:
            FileRegistry instance with loaded entries
        """
        registry = cls(registry_path)
        
        if not Path(registry_path).exists():
            return registry
        
        try:
            with open(registry_path, 'r') as f:
                data = json.load(f)
                
            for entry_data in data.get('entries', []):
                entry = EncryptedFileEntry(**entry_data)
                registry.entries[entry.file_id] = entry
                
        except (json.JSONDecodeError, KeyError, TypeError):
            # If file is corrupted, start with empty registry
            pass
            
        return registry
    
    def save(self) -> None:
        """Save the registry to encrypted_files.json."""
        data = {
            'entries': [asdict(entry) for entry in self.entries.values()]
        }
        
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_entry(self, entry: EncryptedFileEntry) -> None:
        """Add an entry to the registry.
        
        Args:
            entry: The EncryptedFileEntry to add
        """
        self.entries[entry.file_id] = entry
    
    def remove_entry(self, file_id: str) -> None:
        """Remove an entry from the registry.
        
        Args:
            file_id: The unique identifier of the entry to remove
        """
        if file_id in self.entries:
            del self.entries[file_id]
    
    def get_entry(self, file_id: str) -> Optional[EncryptedFileEntry]:
        """Get an entry by file ID.
        
        Args:
            file_id: The unique identifier of the entry
            
        Returns:
            The EncryptedFileEntry if found, None otherwise
        """
        return self.entries.get(file_id)
    
    def list_entries(self) -> list[EncryptedFileEntry]:
        """List all entries in the registry.
        
        Returns:
            List of all EncryptedFileEntry objects
        """
        return list(self.entries.values())
