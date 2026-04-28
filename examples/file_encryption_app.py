"""
Example application demonstrating the File Encryption Manager with MainWindow.

This script shows how to use the MainWindow with the wired encryption workflow.
The MainWindow automatically handles:
1. File selection via dialog
2. File validation using SystemFileValidator
3. Gesture password capture using GestureCapture
4. File encryption using FileEncryptionManager
5. Success/error message display
6. File list refresh

Usage:
    python examples/file_encryption_app.py
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main_window import MainWindow
from src.file_registry import FileRegistry
from src.file_encryption_manager import FileEncryptionManager
from src.gesture_capture import GestureCapture

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Run the File Encryption Manager application."""
    logger.info("Starting File Encryption Manager")
    
    # Load the file registry
    registry = FileRegistry.load()
    
    # Create the main window with optional components
    # If not provided, they will be created automatically when needed
    window = MainWindow(
        registry=registry,
        file_encryption_manager=None,  # Will be created automatically
        gesture_capture=None  # Will be created automatically
    )
    
    # The encryption workflow is already wired in MainWindow._default_add_file_workflow()
    # When the user clicks "Add File":
    # 1. File dialog is shown
    # 2. File is validated (system files, size limits)
    # 3. Gesture password is captured via camera
    # 4. File is encrypted with AES-256-GCM
    # 5. Success/error message is displayed
    # 6. File list is refreshed
    
    logger.info("MainWindow initialized. Click 'Add File' to encrypt a file.")
    
    # Start the GUI event loop
    window.run()
    
    logger.info("Application closed")


if __name__ == "__main__":
    main()
