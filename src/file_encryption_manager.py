"""
File encryption manager - coordinates encryption, validation, and registry management.

This module provides the FileEncryptionManager class that orchestrates the complete
workflow for encrypting, decrypting, and managing encrypted files.
"""

import os
import logging
from typing import Tuple

from src.encryption import EncryptionModule
from src.file_registry import FileRegistry, EncryptedFileEntry
from src.file_validator import SystemFileValidator
from src.config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)


class FileEncryptionManager:
    """
    Core coordinator class for file encryption management.
    
    This class brings together encryption, validation, and registry management
    to provide a complete file encryption workflow. It validates files before
    encryption, handles encryption/decryption operations, manages registry entries,
    and returns (success, message) tuples for all operations.
    """
    
    def __init__(self):
        """Initialize the FileEncryptionManager with required modules."""
        self.encryption = EncryptionModule()
        self.registry = FileRegistry.load()
        self.validator = SystemFileValidator()
        logger.info("FileEncryptionManager initialized")
    
    def encrypt_file(self, file_path: str, gesture_password: list[int]) -> Tuple[bool, str]:
        """
        Encrypt a file with a gesture password.
        
        This method:
        1. Validates the file (system file checks, size limits)
        2. Derives encryption key from gesture password
        3. Encrypts the file with AES-256-GCM
        4. Creates registry entry with metadata
        5. Saves registry to disk
        
        Args:
            file_path: Path to the file to encrypt
            gesture_password: List of gesture integers (5 gestures)
            
        Returns:
            Tuple of (success, message):
            - (True, file_id) if encryption succeeded
            - (False, error_message) if encryption failed
        """
        # Validate file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Validate file against system file checks
        is_valid, error_msg = self.validator.validate_file(file_path)
        if not is_valid:
            logger.warning(f"File validation failed: {error_msg}")
            return False, error_msg
        
        # Validate file size
        is_valid, error_msg = self.validator.validate_file_size(file_path, MAX_FILE_SIZE)
        if not is_valid:
            logger.warning(f"File size validation failed: {error_msg}")
            return False, error_msg
        
        try:
            # Derive encryption key from gesture password
            key = self.encryption.derive_key(gesture_password)
            
            # Encrypt the file
            encrypted_path = self.encryption.encrypt_file(file_path, key)
            
            # Create registry entry
            file_name = os.path.basename(file_path)
            entry = EncryptedFileEntry.create(
                original_path=file_path,
                encrypted_path=encrypted_path,
                gesture_password=gesture_password,
                file_name=file_name
            )
            
            # Add to registry and save
            self.registry.add_entry(entry)
            self.registry.save()
            
            logger.info(f"Successfully encrypted file: {file_path}")
            return True, entry.file_id
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return False, f"Encryption failed: {str(e)}"
    
    def decrypt_file(self, file_id: str, gesture_password: list[int]) -> Tuple[bool, str]:
        """
        Decrypt a file using a gesture password.
        
        This method:
        1. Retrieves registry entry by file_id
        2. Verifies encrypted file exists on disk
        3. Verifies gesture password matches stored password
        4. Derives decryption key from gesture password
        5. Decrypts file to original location
        6. Deletes encrypted file
        7. Removes registry entry
        
        Args:
            file_id: Unique identifier of the encrypted file
            gesture_password: List of gesture integers for verification
            
        Returns:
            Tuple of (success, message):
            - (True, "File decrypted successfully") if decryption succeeded
            - (False, error_message) if decryption failed
        """
        # Get registry entry
        entry = self.registry.get_entry(file_id)
        if entry is None:
            return False, "File not found in registry"
        
        # Verify encrypted file exists
        if not self.verify_encrypted_file_exists(file_id):
            # Remove from registry since file is missing
            self.registry.remove_entry(file_id)
            self.registry.save()
            logger.warning(f"Encrypted file missing, removed from registry: {file_id}")
            return False, "Encrypted file not found on disk"
        
        # Verify gesture password matches
        if entry.gesture_password != gesture_password:
            logger.warning(f"Gesture password mismatch for file: {file_id}")
            return False, "Access Denied"
        
        try:
            # Derive decryption key
            key = self.encryption.derive_key(gesture_password)
            
            # Decrypt file to original location
            self.encryption.decrypt_file(entry.encrypted_path, key, entry.original_path)
            
            # Delete encrypted file
            os.remove(entry.encrypted_path)
            
            # Remove from registry and save
            self.registry.remove_entry(file_id)
            self.registry.save()
            
            logger.info(f"Successfully decrypted file: {entry.original_path}")
            return True, "File decrypted successfully"
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return False, f"Decryption failed: {str(e)}"
    
    def remove_file(self, file_id: str, delete_encrypted: bool) -> Tuple[bool, str]:
        """
        Remove a file from the registry, optionally deleting the encrypted file.
        
        This method:
        1. Retrieves registry entry by file_id
        2. Optionally deletes encrypted file from disk
        3. Removes entry from registry
        4. Saves registry to disk
        
        Args:
            file_id: Unique identifier of the encrypted file
            delete_encrypted: If True, delete the .enc file; if False, only remove from registry
            
        Returns:
            Tuple of (success, message):
            - (True, "File removed successfully") if removal succeeded
            - (False, error_message) if removal failed
        """
        # Get registry entry
        entry = self.registry.get_entry(file_id)
        if entry is None:
            return False, "File not found in registry"
        
        try:
            # Delete encrypted file if requested
            if delete_encrypted:
                if os.path.exists(entry.encrypted_path):
                    os.remove(entry.encrypted_path)
                    logger.info(f"Deleted encrypted file: {entry.encrypted_path}")
                else:
                    logger.warning(f"Encrypted file not found for deletion: {entry.encrypted_path}")
            
            # Remove from registry and save
            self.registry.remove_entry(file_id)
            self.registry.save()
            
            logger.info(f"Removed file from registry: {file_id}")
            return True, "File removed successfully"
            
        except Exception as e:
            logger.error(f"File removal failed: {str(e)}")
            return False, f"File removal failed: {str(e)}"
    
    def verify_encrypted_file_exists(self, file_id: str) -> bool:
        """
        Verify that an encrypted file exists on disk.
        
        Args:
            file_id: Unique identifier of the encrypted file
            
        Returns:
            True if the encrypted file exists, False otherwise
        """
        entry = self.registry.get_entry(file_id)
        if entry is None:
            return False
        
        return os.path.exists(entry.encrypted_path)
