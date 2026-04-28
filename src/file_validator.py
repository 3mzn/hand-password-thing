"""
File validation module for system file protection.

This module provides validation to prevent encryption of critical system files,
hidden files, admin-owned files, and files exceeding size limits.
"""

import os
import stat
from pathlib import Path
from typing import Tuple

from src.config import SYSTEM_DIRS, SYSTEM_EXTENSIONS, MAX_FILE_SIZE


class SystemFileValidator:
    """Validates files before encryption to protect system files."""

    def is_system_file(self, file_path: str) -> bool:
        """
        Check if file is in a Windows system directory.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is in a system directory, False otherwise
        """
        try:
            abs_path = os.path.abspath(file_path)
            
            # Check if file path starts with any system directory
            for sys_dir in SYSTEM_DIRS:
                # Normalize both paths for comparison
                normalized_sys_dir = os.path.normpath(sys_dir)
                normalized_file_path = os.path.normpath(abs_path)
                
                # Check if file is in this system directory
                if normalized_file_path.startswith(normalized_sys_dir):
                    return True
                    
            return False
        except Exception:
            # If we can't determine, err on the side of caution
            return True

    def is_system_extension(self, file_path: str) -> bool:
        """
        Check if file has a protected system extension.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has a system extension, False otherwise
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in SYSTEM_EXTENSIONS

    def is_hidden_file(self, file_path: str) -> bool:
        """
        Check if file is hidden (Windows file attributes).
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is hidden, False otherwise
        """
        try:
            # Check if file exists first
            if not os.path.exists(file_path):
                return False
                
            # On Windows, check FILE_ATTRIBUTE_HIDDEN
            if os.name == 'nt':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
                return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
            else:
                # On Unix-like systems, check if filename starts with dot
                return os.path.basename(file_path).startswith('.')
        except Exception:
            # If we can't determine, err on the side of caution
            return True

    def is_admin_owned(self, file_path: str) -> bool:
        """
        Check if file is owned by administrator/system.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file is admin-owned, False otherwise
        """
        try:
            # Check if file exists first
            if not os.path.exists(file_path):
                return False
                
            # On Windows, check if owner is SYSTEM or Administrators
            if os.name == 'nt':
                import win32security
                
                # Get file security descriptor
                sd = win32security.GetFileSecurity(
                    file_path,
                    win32security.OWNER_SECURITY_INFORMATION
                )
                owner_sid = sd.GetSecurityDescriptorOwner()
                
                # Get well-known SIDs for SYSTEM and Administrators
                system_sid = win32security.ConvertStringSidToSid("S-1-5-18")
                admin_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")
                
                # Check if owner is SYSTEM or Administrators
                return owner_sid == system_sid or owner_sid == admin_sid
            else:
                # On Unix-like systems, check if owned by root (UID 0)
                file_stat = os.stat(file_path)
                return file_stat.st_uid == 0
        except ImportError:
            # win32security not available, can't check ownership
            # Don't block the file on this basis alone
            return False
        except Exception:
            # If we can't determine, don't block on this basis
            return False

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate file against all protection checks.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, "") if file is valid for encryption
            - (False, error_message) if file should not be encrypted
        """
        # Check if file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        # Check system directory
        if self.is_system_file(file_path):
            return False, "Cannot encrypt files in system directories"
        
        # Check system extension
        if self.is_system_extension(file_path):
            return False, "Cannot encrypt files with system extensions"
        
        # Check hidden file
        if self.is_hidden_file(file_path):
            return False, "Cannot encrypt hidden files"
        
        # Check admin ownership
        if self.is_admin_owned(file_path):
            return False, "Cannot encrypt administrator-owned files"
        
        return True, ""

    def validate_file_size(self, file_path: str, max_size: int) -> Tuple[bool, str]:
        """
        Validate file size against maximum limit.
        
        Args:
            file_path: Path to the file to check
            max_size: Maximum allowed file size in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, "") if file size is acceptable
            - (False, error_message) if file is too large
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Check against limit
            if file_size > max_size:
                max_size_mb = max_size / (1024 * 1024)
                return False, f"File size exceeds maximum limit of {max_size_mb:.0f}MB"
            
            return True, ""
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"
