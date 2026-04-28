"""
Encryption module - provides AES-256-GCM encryption for files.

This module handles:
- Key derivation from gesture passwords using SHA-256
- File encryption using AES-256-GCM
- File decryption using AES-256-GCM
"""

from __future__ import annotations
import hashlib
import logging
import os
from typing import List
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)


class EncryptionModule:
    """Handles encryption and decryption of files using AES-256-GCM."""

    @staticmethod
    def derive_key(gesture_password: List[int]) -> bytes:
        """
        Derive an AES-256 encryption key from a gesture password.
        
        The gesture password is a list of integers representing hand gestures.
        This method converts the list to bytes and computes its SHA-256 hash,
        which serves as the 256-bit AES key.
        
        Args:
            gesture_password: List of integers representing gesture sequence
            
        Returns:
            32-byte SHA-256 hash suitable for AES-256 encryption
        """
        # Convert list of integers to bytes
        # Each integer is converted to a single byte
        password_bytes = bytes(gesture_password)
        
        # Compute SHA-256 hash (32 bytes = 256 bits)
        key = hashlib.sha256(password_bytes).digest()
        
        logger.debug("Derived encryption key from gesture password")
        return key

    @staticmethod
    def encrypt_file(file_path: str, key: bytes) -> str:
        """
        Encrypt a file using AES-256-GCM.
        
        Reads the file, encrypts its contents, and writes the encrypted data
        to a new file with .enc extension. The encrypted file contains:
        - 12-byte nonce (prepended)
        - Encrypted data with authentication tag (appended by AESGCM)
        
        Args:
            file_path: Path to the file to encrypt
            key: 32-byte AES-256 encryption key
            
        Returns:
            Path to the encrypted file (original path + .enc)
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            ValueError: If the key is not 32 bytes
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes for AES-256, got {len(key)}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read the file contents
        with open(file_path, 'rb') as f:
            plaintext = f.read()
        
        # Create AESGCM cipher
        aesgcm = AESGCM(key)
        
        # Generate a random 12-byte nonce (96 bits, recommended for GCM)
        nonce = os.urandom(12)
        
        # Encrypt the data (returns ciphertext + 16-byte authentication tag)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Write encrypted file: nonce + ciphertext + tag
        encrypted_path = file_path + '.enc'
        with open(encrypted_path, 'wb') as f:
            f.write(nonce + ciphertext)
        
        logger.info(f"Encrypted file: {file_path} -> {encrypted_path}")
        return encrypted_path

    @staticmethod
    def decrypt_file(encrypted_path: str, key: bytes, output_path: str) -> None:
        """
        Decrypt a file using AES-256-GCM.
        
        Reads the encrypted file, extracts the nonce, and decrypts the contents
        to the specified output path.
        
        Args:
            encrypted_path: Path to the encrypted file (.enc)
            key: 32-byte AES-256 encryption key
            output_path: Path where decrypted file should be written
            
        Raises:
            FileNotFoundError: If the encrypted file doesn't exist
            ValueError: If the key is not 32 bytes or file is too small
            cryptography.exceptions.InvalidTag: If decryption fails (wrong key or corrupted data)
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes for AES-256, got {len(key)}")
        
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
        
        # Read the encrypted file
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Extract nonce (first 12 bytes) and ciphertext (rest)
        if len(encrypted_data) < 12:
            raise ValueError(f"Encrypted file is too small: {len(encrypted_data)} bytes")
        
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        # Create AESGCM cipher and decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        # Write decrypted file
        with open(output_path, 'wb') as f:
            f.write(plaintext)
        
        logger.info(f"Decrypted file: {encrypted_path} -> {output_path}")
