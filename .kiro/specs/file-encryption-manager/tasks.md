# Implementation Plan: File Encryption Manager

## Overview

This implementation extends the existing hand gesture password system into a multi-file encryption manager with a Tkinter GUI. The plan follows an incremental approach: first establishing core encryption and registry infrastructure, then building the GUI layer, and finally integrating gesture capture with the complete workflow.

## Tasks

- [x] 1. Set up dependencies and project configuration
  - Add `cryptography>=41.0.0` to requirements.txt for AES-256-GCM
  - Add `hypothesis>=6.0.0` to requirements.txt for property-based testing
  - Update `src/config.py` with new constants (MAX_FILE_SIZE, SYSTEM_DIRS, SYSTEM_EXTENSIONS, REGISTRY_FILE)
  - _Requirements: 4.1, 4.2, 5.1, 10.1_

- [ ] 2. Implement encryption module
  - [x] 2.1 Create `src/encryption.py` with EncryptionModule class
    - Implement `derive_key(gesture_password: list[int]) -> bytes` using SHA-256
    - Implement `encrypt_file(file_path: str, key: bytes) -> str` using AES-256-GCM
    - Implement `decrypt_file(encrypted_path: str, key: bytes, output_path: str) -> None`
    - _Requirements: 1.3, 1.4, 2.3, 11.2, 11.3, 11.4_

  - [ ]* 2.2 Write property test for encryption round-trip
    - **Property 1: Round-trip consistency**
    - **Validates: Requirements 11.5**

  - [ ]* 2.3 Write unit tests for EncryptionModule
    - Test key derivation with known gesture sequences
    - Test encryption/decryption with sample files
    - Test error handling for invalid keys
    - _Requirements: 1.3, 1.4, 2.3_

- [ ] 3. Implement file validation module
  - [x] 3.1 Create `src/file_validator.py` with SystemFileValidator class
    - Implement `is_system_file(file_path: str) -> bool` checking Windows system directories
    - Implement `is_system_extension(file_path: str) -> bool` checking protected extensions
    - Implement `is_hidden_file(file_path: str) -> bool` checking file attributes
    - Implement `is_admin_owned(file_path: str) -> bool` checking file ownership
    - Implement `validate_file(file_path: str) -> tuple[bool, str]` combining all checks
    - Implement `validate_file_size(file_path: str, max_size: int) -> tuple[bool, str]`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1_

  - [ ]* 3.2 Write unit tests for SystemFileValidator
    - Test system directory detection
    - Test system extension detection
    - Test file size validation
    - Test validation error messages
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1_

- [ ] 4. Implement file registry module
  - [x] 4.1 Create `src/file_registry.py` with EncryptedFileEntry and FileRegistry classes
    - Implement EncryptedFileEntry dataclass with fields: file_id, original_path, encrypted_path, gesture_password, file_name
    - Implement `FileRegistry.load() -> FileRegistry` loading from encrypted_files.json
    - Implement `FileRegistry.save() -> None` saving to encrypted_files.json
    - Implement `FileRegistry.add_entry(entry: EncryptedFileEntry) -> None`
    - Implement `FileRegistry.remove_entry(file_id: str) -> None`
    - Implement `FileRegistry.get_entry(file_id: str) -> EncryptedFileEntry | None`
    - Implement `FileRegistry.list_entries() -> list[EncryptedFileEntry]`
    - _Requirements: 1.6, 2.5, 3.2, 3.3, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 4.2 Write property test for registry persistence
    - **Property 5: Registry persistence**
    - **Validates: Requirements 10.3, 10.4**

  - [ ]* 4.3 Write unit tests for FileRegistry
    - Test adding and removing entries
    - Test loading from non-existent file
    - Test save/load round-trip
    - _Requirements: 1.6, 2.5, 10.3, 10.4_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Refactor gesture capture into reusable module
  - [x] 6.1 Create `src/gesture_capture.py` with GestureCapture class
    - Extract gesture capture logic from existing `src/main.py`
    - Implement `capture_gesture_password(mode: str) -> list[int] | None` supporting "enroll" and "verify" modes
    - Implement `_display_instructions(mode: str) -> None` showing mode-specific instructions
    - Reuse existing `HandCapture` and gesture detection functions
    - _Requirements: 1.2, 2.1, 9.3_

  - [ ]* 6.2 Write unit tests for GestureCapture
    - Test gesture sequence validation
    - Test mode handling
    - _Requirements: 1.2, 2.1_

- [ ] 7. Implement main window GUI
  - [x] 7.1 Create `src/main_window.py` with MainWindow class
    - Implement Tkinter window with title "File Encryption Manager"
    - Implement file list display showing file name and original location
    - Implement "Add File" button triggering file browser dialog
    - Implement "Decrypt" button for each file entry
    - Implement "Remove" button for each file entry
    - Implement `refresh_file_list() -> None` updating display from registry
    - _Requirements: 1.1, 2.1, 6.1, 6.2, 6.3, 9.1, 9.2_

  - [ ]* 7.2 Write unit tests for MainWindow
    - Test window initialization
    - Test file list refresh
    - Test button creation
    - _Requirements: 6.1, 6.2, 6.3, 9.1, 9.2_

- [ ] 8. Implement file encryption manager core
  - [x] 8.1 Create `src/file_encryption_manager.py` with FileEncryptionManager class
    - Implement `__init__` initializing EncryptionModule, FileRegistry, SystemFileValidator
    - Implement `encrypt_file(file_path: str, gesture_password: list[int]) -> tuple[bool, str]`
    - Implement `decrypt_file(file_id: str, gesture_password: list[int]) -> tuple[bool, str]`
    - Implement `remove_file(file_id: str, delete_encrypted: bool) -> tuple[bool, str]`
    - Implement `verify_encrypted_file_exists(file_id: str) -> bool`
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 2.2, 2.3, 2.4, 2.5, 3.2, 3.3, 7.1, 7.2, 7.3_

  - [ ]* 8.2 Write property test for gesture password verification
    - **Property 3: Gesture password verification**
    - **Validates: Requirements 2.2, 2.7**

  - [ ]* 8.3 Write property test for file naming consistency
    - **Property 6: File naming consistency**
    - **Validates: Requirements 8.1, 8.2**

  - [ ]* 8.4 Write unit tests for FileEncryptionManager
    - Test successful encryption workflow
    - Test successful decryption workflow
    - Test incorrect gesture password handling
    - Test file removal with and without deletion
    - _Requirements: 1.3, 1.4, 1.5, 2.2, 2.3, 2.4, 3.2, 3.3_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Integrate workflows in main window
  - [x] 10.1 Wire encryption workflow in MainWindow
    - Connect "Add File" button to file browser dialog
    - Call SystemFileValidator to validate selected file
    - Call GestureCapture for password enrollment
    - Call FileEncryptionManager.encrypt_file
    - Display success/error messages
    - Refresh file list on success
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 4.5, 5.2, 9.3, 9.4_

  - [x] 10.2 Wire decryption workflow in MainWindow
    - Connect "Decrypt" button to GestureCapture for verification
    - Call FileEncryptionManager.decrypt_file
    - Handle missing file scenario
    - Display success/error messages
    - Refresh file list on success
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 7.1, 7.2, 7.3, 7.4, 9.3, 9.4_

  - [x] 10.3 Wire removal workflow in MainWindow
    - Connect "Remove" button to confirmation dialog
    - Call FileEncryptionManager.remove_file with user choice
    - Refresh file list after removal
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 10.4 Write integration tests for complete workflows
    - Test end-to-end encryption workflow
    - Test end-to-end decryption workflow
    - Test end-to-end removal workflow
    - Test missing file handling
    - _Requirements: 1.1-1.7, 2.1-2.7, 3.1-3.4, 7.1-7.4_

- [ ] 11. Create application entry point
  - [x] 11.1 Create `src/app.py` as main entry point
    - Initialize FileEncryptionManager
    - Initialize and display MainWindow
    - Set up Tkinter event loop
    - _Requirements: 9.1, 9.2, 10.3_

  - [x] 11.2 Update `src/main.py` or create migration guide
    - Document transition from old single-password system to new multi-file manager
    - Preserve backward compatibility if needed or provide migration instructions
    - _Requirements: 9.1_

- [ ] 12. Implement remaining property-based tests
  - [ ]* 12.1 Write property test for registry entry uniqueness
    - **Property 4: Registry entry uniqueness**
    - **Validates: Requirements 1.6, 10.2**

  - [ ]* 12.2 Write property test for file overwrite behavior
    - **Property 7: File overwrite behavior**
    - **Validates: Requirements 8.3**

  - [ ]* 12.3 Write property test for system file rejection
    - **Property 8: System file rejection**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

  - [ ]* 12.4 Write property test for file size limit enforcement
    - **Property 9: File size limit enforcement**
    - **Validates: Requirements 5.1, 5.2**

  - [ ]* 12.5 Write property test for registry capacity
    - **Property 10: Registry capacity**
    - **Validates: Requirements 5.3**

  - [ ]* 12.6 Write property test for missing file cleanup
    - **Property 11: Missing file cleanup**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

  - [ ]* 12.7 Write property test for GUI state consistency
    - **Property 12: GUI state consistency**
    - **Validates: Requirements 6.4**

  - [ ]* 12.8 Write property test for data persistence across sessions
    - **Property 13: Data persistence across sessions**
    - **Validates: Requirements 10.3, 10.4**

  - [ ]* 12.9 Write property test for encryption key determinism
    - **Property 14: Encryption key determinism**
    - **Validates: Requirements 11.2, 11.3, 11.4**

  - [ ]* 12.10 Write property test for gesture password storage
    - **Property 15: Gesture password storage**
    - **Validates: Requirements 10.5**

  - [ ]* 12.11 Write property test for file path preservation
    - **Property 16: File path preservation**
    - **Validates: Requirements 1.5, 1.6, 2.3**

  - [ ]* 12.12 Write property test for concurrent registry operations
    - **Property 17: Concurrent registry operations**
    - **Validates: Requirements 10.4**

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation reuses existing `HandCapture` and gesture detection from the current codebase
- The old `src/password_store.py` will be deprecated in favor of the new FileRegistry
- Property-based tests use the `hypothesis` library for generating test cases
- Integration tests should use temporary directories and files to avoid affecting the user's system
