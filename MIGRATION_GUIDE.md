# Migration Guide: Gesture Lock → File Encryption Manager

## Overview

This project has evolved from a **single-password gesture lock system** to a **multi-file encryption manager**. This guide explains the differences and how to transition between the two systems.

## What Changed?

### Old System (`src/main.py`)
- **Purpose**: Single gesture password authentication system
- **Use Case**: Unlock access by verifying a 5-gesture password
- **Interface**: OpenCV window with keyboard controls (E/V/R/Q)
- **Storage**: In-memory password storage (not persistent)
- **Workflow**: Enroll → Verify → Show unlock code

### New System (`src/app.py`)
- **Purpose**: Multi-file encryption manager with gesture passwords
- **Use Case**: Encrypt/decrypt multiple files, each with unique gesture passwords
- **Interface**: Tkinter GUI with file browser and management controls
- **Storage**: Persistent file registry (`encrypted_files.json`) and encrypted files on disk
- **Workflow**: Add files → Encrypt with gestures → Manage encrypted files → Decrypt when needed

## Key Differences

| Feature | Old System | New System |
|---------|-----------|------------|
| **Entry Point** | `python -m src.main` | `python -m src.app` |
| **Password Count** | Single password | Unlimited (one per file) |
| **Persistence** | None (in-memory) | Full (JSON registry + .enc files) |
| **UI Framework** | OpenCV | Tkinter + OpenCV |
| **Primary Function** | Authentication | File encryption/decryption |
| **Gesture Count** | 5 gestures | 5 gestures (unchanged) |
| **Encryption** | None | AES-256-GCM |

## Running Each System

### Old Gesture Lock System
```bash
# Activate virtual environment
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Unix/macOS

# Run the gesture lock
python -m src.main

# Controls:
# E - Enroll new password
# V - Verify password
# R - Reset
# Q - Quit
```

### New File Encryption Manager
```bash
# Activate virtual environment
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Unix/macOS

# Run the file encryption manager
python -m src.app

# GUI Controls:
# - Click "Add File" to encrypt a new file
# - Click "Decrypt" to decrypt and restore a file
# - Click "Remove" to remove a file from the list
```

## Migration Scenarios

### Scenario 1: You Want to Keep Using the Old System
**No action needed.** The old system (`src/main.py`) remains fully functional and unchanged. Continue using `python -m src.main`.

### Scenario 2: You Want to Switch to the New System
1. **Understand the difference**: The new system encrypts actual files, not just authentication
2. **Run the new system**: Use `python -m src.app` instead of `python -m src.main`
3. **Start fresh**: The new system has its own file registry and doesn't use the old password

### Scenario 3: You Want to Use Both Systems
Both systems can coexist:
- **Old system**: `python -m src.main` for gesture authentication
- **New system**: `python -m src.app` for file encryption
- They operate independently and don't interfere with each other

## Technical Details

### Shared Components
Both systems share the core gesture detection infrastructure:
- `src/gesture.py` - Finger state detection and gesture classification
- `src/capture.py` - MediaPipe hand tracking (used by old system)
- `src/gesture_capture.py` - Enhanced capture for new system
- `src/config.py` - Configuration constants

### New Components (File Encryption Manager Only)
- `src/app.py` - Main entry point for GUI application
- `src/main_window.py` - Tkinter GUI for file management
- `src/file_encryption_manager.py` - Core encryption/decryption logic
- `src/encryption.py` - AES-256-GCM encryption implementation
- `src/password_store.py` - Gesture password storage and verification
- `src/file_validator.py` - System file protection and validation
- `encrypted_files.json` - Persistent file registry (created on first run)

### Encryption Details
The new system uses:
- **Algorithm**: AES-256-GCM (authenticated encryption)
- **Key Derivation**: SHA-256 hash of gesture password binary representation
- **File Format**: Original filename + `.enc` extension
- **Storage**: Encrypted files stored in their original locations
- **Registry**: JSON file tracking all encrypted files and their gesture passwords

## Security Considerations

### Old System
- Passwords stored in memory only (not persistent)
- No actual data encryption
- Suitable for demonstration and authentication testing

### New System
- Gesture passwords stored in plaintext in `encrypted_files.json`
- Files encrypted with AES-256-GCM
- System file protection prevents encrypting critical OS files
- 100MB file size limit for performance
- **Important**: Keep `encrypted_files.json` secure - it contains gesture passwords

## Troubleshooting

### "I can't find my encrypted files"
- Check `encrypted_files.json` for the file registry
- Encrypted files have `.enc` extension and are in their original locations
- Use the GUI's file list to see all encrypted files

### "The old system doesn't work anymore"
- The old system (`src/main.py`) is unchanged and should work
- Make sure you're using `python -m src.main`, not `python -m src.app`
- Check that dependencies are installed: `pip install -e .`

### "I want to go back to the old system"
- Simply run `python -m src.main` instead of `python -m src.app`
- Both systems coexist independently

## Recommendations

### For Authentication Testing
Use the **old system** (`src/main.py`):
- Faster workflow for testing gesture recognition
- No file management overhead
- In-memory operation

### For File Protection
Use the **new system** (`src/app.py`):
- Encrypt sensitive documents
- Manage multiple encrypted files
- Persistent storage and recovery

## Support

For issues or questions:
1. Check the README.md for basic usage
2. Review this migration guide for system differences
3. Check the requirements document: `.kiro/specs/file-encryption-manager/requirements.md`

## Future Considerations

The old system (`src/main.py`) is maintained for backward compatibility and testing purposes. Future development will focus on the new File Encryption Manager system.
