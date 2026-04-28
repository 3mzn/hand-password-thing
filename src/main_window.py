"""
Main window GUI for the File Encryption Manager.

This module provides the MainWindow class which displays the list of
encrypted files and provides controls for adding, decrypting, and removing files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
import logging

from src.file_registry import FileRegistry, EncryptedFileEntry

logger = logging.getLogger(__name__)


class MainWindow:
    """Main GUI window for managing encrypted files.
    
    Displays a list of encrypted files with controls for each file
    (Decrypt, Remove) and a global "Add File" button.
    """
    
    def __init__(self, registry: FileRegistry, file_encryption_manager=None, gesture_capture=None):
        """Initialize the main window.
        
        Args:
            registry: FileRegistry instance for accessing encrypted file data
            file_encryption_manager: Optional FileEncryptionManager instance for encryption operations
            gesture_capture: Optional GestureCapture instance for capturing gesture passwords
        """
        self.registry = registry
        self.file_encryption_manager = file_encryption_manager
        self.gesture_capture = gesture_capture
        
        self.root = tk.Tk()
        self.root.title("File Encryption Manager")
        self.root.geometry("800x600")
        
        # Callbacks for button actions (to be set by the controller)
        self.on_add_file: Optional[Callable[[], None]] = None
        self.on_decrypt_file: Optional[Callable[[str], None]] = None
        self.on_remove_file: Optional[Callable[[str], None]] = None
        
        self._setup_ui()
        self.refresh_file_list()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Title label
        title_label = tk.Label(
            self.root,
            text="File Encryption Manager",
            font=("Arial", 16, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Add File button at the top
        add_button = tk.Button(
            self.root,
            text="Add File",
            command=self._handle_add_file,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        add_button.pack(pady=10)
        
        # Frame for file list with scrollbar
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrollable content
        self.canvas = tk.Canvas(list_frame, yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        # Frame inside canvas to hold file entries
        self.file_list_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.file_list_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.file_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
    
    def _handle_add_file(self) -> None:
        """Handle Add File button click.
        
        Implements the complete encryption workflow:
        1. Show file dialog
        2. Validate the file
        3. Capture gesture password
        4. Encrypt the file
        5. Show success/error messages
        6. Refresh file list
        """
        if self.on_add_file:
            self.on_add_file()
        else:
            # Default implementation if no callback is set
            self._default_add_file_workflow()
    
    def _handle_decrypt_file(self, file_id: str) -> None:
        """Handle Decrypt button click for a specific file.
        
        Implements the complete decryption workflow:
        1. Capture gesture password using GestureCapture in "verify" mode
        2. Call FileEncryptionManager.decrypt_file
        3. Handle "Access Denied" for wrong passwords
        4. Handle missing encrypted files
        5. Show success/error messages
        6. Refresh file list on success
        
        Args:
            file_id: The unique identifier of the file to decrypt
        """
        if self.on_decrypt_file:
            self.on_decrypt_file(file_id)
        else:
            # Default implementation if no callback is set
            self._default_decrypt_file_workflow(file_id)
    
    def _handle_remove_file(self, file_id: str) -> None:
        """Handle Remove button click for a specific file.
        
        Implements the complete removal workflow:
        1. Show confirmation dialog asking whether to delete .enc file or just remove from list
        2. Call FileEncryptionManager.remove_file with user choice
        3. Refresh file list after removal
        
        Args:
            file_id: The unique identifier of the file to remove
        """
        if self.on_remove_file:
            self.on_remove_file(file_id)
        else:
            # Default implementation if no callback is set
            self._default_remove_file_workflow(file_id)
    
    def refresh_file_list(self) -> None:
        """Update the file list display from the registry.
        
        Clears the current display and rebuilds it with all entries
        from the FileRegistry.
        """
        # Clear existing widgets
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        
        # Get all entries from registry
        entries = self.registry.list_entries()
        
        if not entries:
            # Display message when no files are encrypted
            no_files_label = tk.Label(
                self.file_list_frame,
                text="No encrypted files. Click 'Add File' to get started.",
                font=("Arial", 12),
                fg="gray",
                pady=50
            )
            no_files_label.pack()
            return
        
        # Create a frame for each file entry
        for entry in entries:
            self._create_file_entry_widget(entry)
    
    def _create_file_entry_widget(self, entry: EncryptedFileEntry) -> None:
        """Create a widget displaying a single file entry.
        
        Args:
            entry: The EncryptedFileEntry to display
        """
        # Container frame for this file entry
        entry_frame = tk.Frame(
            self.file_list_frame,
            relief=tk.RAISED,
            borderwidth=2,
            padx=10,
            pady=10
        )
        entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Left side: File information
        info_frame = tk.Frame(entry_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # File name (bold)
        name_label = tk.Label(
            info_frame,
            text=entry.file_name,
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        # Original location (smaller, gray)
        location_label = tk.Label(
            info_frame,
            text=f"Location: {entry.original_path}",
            font=("Arial", 9),
            fg="gray",
            anchor="w"
        )
        location_label.pack(anchor="w")
        
        # Right side: Action buttons
        button_frame = tk.Frame(entry_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # Decrypt button
        decrypt_button = tk.Button(
            button_frame,
            text="Decrypt",
            command=lambda: self._handle_decrypt_file(entry.file_id),
            font=("Arial", 10),
            bg="#2196F3",
            fg="white",
            padx=15,
            pady=5
        )
        decrypt_button.pack(side=tk.LEFT, padx=5)
        
        # Remove button
        remove_button = tk.Button(
            button_frame,
            text="Remove",
            command=lambda: self._handle_remove_file(entry.file_id),
            font=("Arial", 10),
            bg="#f44336",
            fg="white",
            padx=15,
            pady=5
        )
        remove_button.pack(side=tk.LEFT, padx=5)
    
    def show_file_dialog(self) -> Optional[str]:
        """Display a file browser dialog for selecting a file to encrypt.
        
        Returns:
            The selected file path, or None if cancelled
        """
        file_path = filedialog.askopenfilename(
            title="Select a file to encrypt",
            filetypes=[("All files", "*.*")]
        )
        return file_path if file_path else None
    
    def show_error(self, message: str) -> None:
        """Display an error message dialog.
        
        Args:
            message: The error message to display
        """
        messagebox.showerror("Error", message)
    
    def show_success(self, message: str) -> None:
        """Display a success message dialog.
        
        Args:
            message: The success message to display
        """
        messagebox.showinfo("Success", message)
    
    def show_info(self, message: str) -> None:
        """Display an information message dialog.
        
        Args:
            message: The information message to display
        """
        messagebox.showinfo("Information", message)
    
    def ask_delete_confirmation(self) -> bool:
        """Ask user whether to delete the .enc file or just remove from list.
        
        Returns:
            True if user wants to delete the file, False to just remove from list
        """
        result = messagebox.askyesnocancel(
            "Delete .enc file?",
            "Do you want to delete the encrypted file from disk?\n\n"
            "Yes: Delete the .enc file\n"
            "No: Remove from list only\n"
            "Cancel: Keep in list"
        )
        return result  # True, False, or None
    
    def _default_add_file_workflow(self) -> None:
        """Default implementation of the add file workflow.
        
        This method implements the complete encryption workflow:
        1. Show file dialog
        2. Validate the file using SystemFileValidator
        3. Capture gesture password using GestureCapture
        4. Encrypt the file using FileEncryptionManager
        5. Show success/error messages
        6. Refresh file list on success
        
        This requires file_encryption_manager and gesture_capture to be set.
        """
        # Step 1: Show file browser dialog
        file_path = self.show_file_dialog()
        if not file_path:
            # User cancelled
            return
        
        logger.info(f"User selected file: {file_path}")
        
        # Import here to avoid circular dependencies
        try:
            from src.file_encryption_manager import FileEncryptionManager
            from src.gesture_capture import GestureCapture
        except ImportError as e:
            self.show_error(f"Failed to import required modules: {str(e)}\n\nPlease ensure all dependencies are installed:\npip install -r requirements.txt")
            logger.error(f"Import error: {str(e)}")
            return
        
        # Ensure we have the required components
        if self.file_encryption_manager is None:
            self.file_encryption_manager = FileEncryptionManager()
        
        if self.gesture_capture is None:
            try:
                self.gesture_capture = GestureCapture()
            except Exception as e:
                self.show_error(f"Failed to initialize gesture capture: {str(e)}\n\nPlease ensure MediaPipe is installed correctly:\npip install mediapipe>=0.10.0")
                logger.error(f"GestureCapture initialization error: {str(e)}")
                return
        
        # Step 2: Validate the file (validation is done inside encrypt_file)
        # Step 3: Capture gesture password for enrollment
        logger.info("Starting gesture password enrollment")
        try:
            gesture_password = self.gesture_capture.capture_gesture_password("enroll")
        except Exception as e:
            self.show_error(f"Gesture capture failed: {str(e)}")
            logger.error(f"Gesture capture error: {str(e)}")
            return
        
        if gesture_password is None:
            # User cancelled gesture capture
            self.show_info("Gesture capture cancelled")
            return
        
        logger.info("Gesture password captured successfully")
        
        # Step 4: Encrypt the file using FileEncryptionManager
        success, message = self.file_encryption_manager.encrypt_file(file_path, gesture_password)
        
        # Step 5: Display success/error messages
        if success:
            self.show_success(f"File encrypted successfully!\nFile ID: {message}")
            logger.info(f"File encrypted successfully: {file_path}")
            
            # Step 6: Refresh file list on success
            self.refresh_file_list()
        else:
            self.show_error(f"Encryption failed: {message}")
            logger.error(f"Encryption failed for {file_path}: {message}")
    
    def _default_decrypt_file_workflow(self, file_id: str) -> None:
        """Default implementation of the decrypt file workflow.
        
        This method implements the complete decryption workflow:
        1. Capture gesture password using GestureCapture in "verify" mode
        2. Call FileEncryptionManager.decrypt_file
        3. Handle "Access Denied" for wrong passwords
        4. Handle missing encrypted files
        5. Show success/error messages
        6. Refresh file list on success
        
        Args:
            file_id: The unique identifier of the file to decrypt
        """
        logger.info(f"Starting decryption workflow for file: {file_id}")
        
        # Import here to avoid circular dependencies
        from src.file_encryption_manager import FileEncryptionManager
        from src.gesture_capture import GestureCapture
        
        # Ensure we have the required components
        if self.file_encryption_manager is None:
            self.file_encryption_manager = FileEncryptionManager()
        
        if self.gesture_capture is None:
            self.gesture_capture = GestureCapture()
        
        # Step 1: Capture gesture password for verification
        logger.info("Starting gesture password verification")
        gesture_password = self.gesture_capture.capture_gesture_password("verify")
        
        if gesture_password is None:
            # User cancelled gesture capture
            self.show_info("Gesture verification cancelled")
            return
        
        logger.info("Gesture password captured for verification")
        
        # Step 2: Call FileEncryptionManager.decrypt_file
        success, message = self.file_encryption_manager.decrypt_file(file_id, gesture_password)
        
        # Step 3-5: Handle results and display messages
        if success:
            # Success case
            self.show_success(message)
            logger.info(f"File decrypted successfully: {file_id}")
            
            # Step 6: Refresh file list on success
            self.refresh_file_list()
        else:
            # Error cases
            if message == "Access Denied":
                # Wrong password
                self.show_error("Access Denied: Incorrect gesture password")
                logger.warning(f"Access denied for file: {file_id}")
            elif message == "Encrypted file not found on disk":
                # Missing file - already removed from registry by FileEncryptionManager
                self.show_error("Encrypted file not found on disk. Removed from list.")
                logger.warning(f"Missing encrypted file removed: {file_id}")
                # Refresh to show updated list
                self.refresh_file_list()
            else:
                # Other errors
                self.show_error(f"Decryption failed: {message}")
                logger.error(f"Decryption failed for {file_id}: {message}")
    
    def _default_remove_file_workflow(self, file_id: str) -> None:
        """Default implementation of the remove file workflow.
        
        This method implements the complete removal workflow:
        1. Show confirmation dialog asking whether to delete .enc file or just remove from list
        2. Call FileEncryptionManager.remove_file with user choice
        3. Refresh file list after removal
        
        The dialog has three options:
        - Yes: Delete the .enc file from disk and remove from list
        - No: Remove from list only (keep .enc file)
        - Cancel: Keep in list (do nothing)
        
        Args:
            file_id: The unique identifier of the file to remove
        """
        logger.info(f"Starting removal workflow for file: {file_id}")
        
        # Import here to avoid circular dependencies
        from src.file_encryption_manager import FileEncryptionManager
        
        # Ensure we have the required components
        if self.file_encryption_manager is None:
            self.file_encryption_manager = FileEncryptionManager()
        
        # Step 1: Show confirmation dialog
        result = self.ask_delete_confirmation()
        
        if result is None:
            # User clicked Cancel - keep in list
            logger.info("User cancelled removal")
            return
        
        # Step 2: Call FileEncryptionManager.remove_file with user choice
        # result is True (delete file) or False (remove from list only)
        delete_encrypted = result
        success, message = self.file_encryption_manager.remove_file(file_id, delete_encrypted)
        
        # Step 3: Handle results and refresh file list
        if success:
            if delete_encrypted:
                self.show_success("File deleted and removed from list")
                logger.info(f"File deleted and removed: {file_id}")
            else:
                self.show_success("File removed from list (encrypted file kept)")
                logger.info(f"File removed from list only: {file_id}")
            
            # Refresh file list after removal
            self.refresh_file_list()
        else:
            # Error case
            self.show_error(f"Removal failed: {message}")
            logger.error(f"Removal failed for {file_id}: {message}")
    
    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
    
    def close(self) -> None:
        """Close the main window."""
        self.root.destroy()
