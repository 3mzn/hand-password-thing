"""
Unit tests for the encryption module.
"""

import os
import tempfile
import pytest
from cryptography.exceptions import InvalidTag
from src.encryption import EncryptionModule


class TestEncryptionModule:
    """Test cases for EncryptionModule."""

    def test_derive_key_returns_32_bytes(self):
        """Test that derive_key returns a 32-byte key."""
        gesture_password = [1, 2, 3, 4, 5]
        key = EncryptionModule.derive_key(gesture_password)
        assert len(key) == 32
        assert isinstance(key, bytes)

    def test_derive_key_deterministic(self):
        """Test that the same password produces the same key."""
        gesture_password = [1, 2, 3, 4, 5]
        key1 = EncryptionModule.derive_key(gesture_password)
        key2 = EncryptionModule.derive_key(gesture_password)
        assert key1 == key2

    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        key1 = EncryptionModule.derive_key([1, 2, 3, 4, 5])
        key2 = EncryptionModule.derive_key([5, 4, 3, 2, 1])
        assert key1 != key2

    def test_encrypt_decrypt_round_trip(self):
        """Test that encrypting and decrypting produces the original content."""
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            test_content = b"This is a test file for encryption."
            f.write(test_content)
            temp_file = f.name

        try:
            # Derive key and encrypt
            gesture_password = [1, 2, 3, 4, 5]
            key = EncryptionModule.derive_key(gesture_password)
            encrypted_path = EncryptionModule.encrypt_file(temp_file, key)

            # Verify encrypted file exists and has .enc extension
            assert os.path.exists(encrypted_path)
            assert encrypted_path == temp_file + '.enc'

            # Decrypt to a new file
            decrypted_path = temp_file + '.decrypted'
            EncryptionModule.decrypt_file(encrypted_path, key, decrypted_path)

            # Verify decrypted content matches original
            with open(decrypted_path, 'rb') as f:
                decrypted_content = f.read()
            assert decrypted_content == test_content

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            if os.path.exists(decrypted_path):
                os.remove(decrypted_path)

    def test_encrypt_file_not_found(self):
        """Test that encrypting a non-existent file raises FileNotFoundError."""
        key = EncryptionModule.derive_key([1, 2, 3, 4, 5])
        with pytest.raises(FileNotFoundError):
            EncryptionModule.encrypt_file('/nonexistent/file.txt', key)

    def test_decrypt_file_not_found(self):
        """Test that decrypting a non-existent file raises FileNotFoundError."""
        key = EncryptionModule.derive_key([1, 2, 3, 4, 5])
        with pytest.raises(FileNotFoundError):
            EncryptionModule.decrypt_file('/nonexistent/file.enc', key, '/tmp/output.txt')

    def test_decrypt_with_wrong_key(self):
        """Test that decrypting with wrong key raises InvalidTag."""
        # Create and encrypt a file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Secret content")
            temp_file = f.name

        try:
            # Encrypt with one key
            key1 = EncryptionModule.derive_key([1, 2, 3, 4, 5])
            encrypted_path = EncryptionModule.encrypt_file(temp_file, key1)

            # Try to decrypt with different key
            key2 = EncryptionModule.derive_key([5, 4, 3, 2, 1])
            decrypted_path = temp_file + '.decrypted'

            with pytest.raises(InvalidTag):
                EncryptionModule.decrypt_file(encrypted_path, key2, decrypted_path)

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            if os.path.exists(decrypted_path):
                os.remove(decrypted_path)

    def test_encrypt_with_invalid_key_length(self):
        """Test that encrypting with wrong key length raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b"Test content")
            temp_file = f.name

        try:
            invalid_key = b"short_key"  # Not 32 bytes
            with pytest.raises(ValueError, match="Key must be 32 bytes"):
                EncryptionModule.encrypt_file(temp_file, invalid_key)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_decrypt_with_invalid_key_length(self):
        """Test that decrypting with wrong key length raises ValueError."""
        invalid_key = b"short_key"  # Not 32 bytes
        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            EncryptionModule.decrypt_file('/tmp/file.enc', invalid_key, '/tmp/output.txt')

    def test_encrypt_empty_file(self):
        """Test that encrypting an empty file works correctly."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            temp_file = f.name  # Empty file

        try:
            key = EncryptionModule.derive_key([1, 2, 3, 4, 5])
            encrypted_path = EncryptionModule.encrypt_file(temp_file, key)

            # Decrypt and verify
            decrypted_path = temp_file + '.decrypted'
            EncryptionModule.decrypt_file(encrypted_path, key, decrypted_path)

            with open(decrypted_path, 'rb') as f:
                content = f.read()
            assert content == b""

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            if os.path.exists(decrypted_path):
                os.remove(decrypted_path)

    def test_encrypt_binary_file(self):
        """Test that encrypting binary data works correctly."""
        # Create a file with binary data
        binary_data = bytes(range(256))  # All byte values 0-255
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(binary_data)
            temp_file = f.name

        try:
            key = EncryptionModule.derive_key([1, 2, 3, 4, 5])
            encrypted_path = EncryptionModule.encrypt_file(temp_file, key)

            # Decrypt and verify
            decrypted_path = temp_file + '.decrypted'
            EncryptionModule.decrypt_file(encrypted_path, key, decrypted_path)

            with open(decrypted_path, 'rb') as f:
                decrypted_data = f.read()
            assert decrypted_data == binary_data

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            if os.path.exists(decrypted_path):
                os.remove(decrypted_path)
