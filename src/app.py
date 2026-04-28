"""
Main entry point for the File Encryption Manager application.

This module initializes the FileEncryptionManager and MainWindow,
then starts the Tkinter event loop.

Usage:
    python -m src.app
    OR
    python src/app.py
"""

import logging
import os
import sys

# Add parent directory to path if running directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.file_encryption_manager import FileEncryptionManager
from src.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting File Encryption Manager")
        
        # Initialize FileEncryptionManager
        manager = FileEncryptionManager()
        logger.info("FileEncryptionManager initialized")
        
        # Initialize MainWindow with the registry from the manager
        window = MainWindow(
            registry=manager.registry,
            file_encryption_manager=manager
        )
        logger.info("MainWindow initialized")
        
        # Start the Tkinter event loop
        logger.info("Starting GUI event loop")
        window.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
