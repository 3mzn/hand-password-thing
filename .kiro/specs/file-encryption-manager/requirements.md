# Requirements Document

## Introduction

This feature extends the existing hand gesture password authentication system into a multi-file encryption manager. Users can encrypt multiple files using unique gesture passwords (sequences of 5 hand gestures) and manage them through a Tkinter GUI. The system integrates with the existing MediaPipe gesture detection infrastructure to provide secure file encryption using AES-256-GCM.

## Glossary

- **File_Encryption_Manager**: The system that manages encrypted files and their associated gesture passwords
- **Gesture_Password**: A sequence of 5 hand gestures (Fist, One, Two, Three, Four, Five) used as authentication
- **Encrypted_File**: A file encrypted with AES-256-GCM and stored with .enc extension
- **File_Registry**: JSON configuration file (encrypted_files.json) storing metadata for all encrypted files
- **Main_Window**: Tkinter GUI displaying the list of encrypted files and management controls
- **Camera_Window**: OpenCV window for capturing hand gestures during enrollment and verification
- **System_File**: Files in protected Windows directories or with protected extensions
- **Original_Location**: The file path where the unencrypted file was located before encryption
- **Gesture_Detector**: The existing MediaPipe-based component that recognizes hand gestures
- **Encryption_Key**: AES-256 key derived from the SHA-256 hash of the gesture password

## Requirements

### Requirement 1: File Encryption

**User Story:** As a user, I want to encrypt files with gesture passwords, so that I can protect sensitive data.

#### Acceptance Criteria

1. WHEN a user selects a file for encryption, THE File_Encryption_Manager SHALL display a file browser dialog
2. WHEN a user selects a valid file, THE File_Encryption_Manager SHALL open the Camera_Window for gesture password enrollment
3. WHEN a user completes gesture password enrollment, THE File_Encryption_Manager SHALL derive an Encryption_Key using SHA-256 hash of the gesture password
4. WHEN an Encryption_Key is derived, THE File_Encryption_Manager SHALL encrypt the file using AES-256-GCM
5. WHEN encryption completes, THE File_Encryption_Manager SHALL save the encrypted file with .enc extension in the Original_Location
6. WHEN an encrypted file is saved, THE File_Encryption_Manager SHALL add an entry to the File_Registry with file ID, original path, encrypted path, gesture password, and file name
7. WHEN a File_Registry entry is created, THE File_Encryption_Manager SHALL display the encrypted file in the Main_Window

### Requirement 2: File Decryption

**User Story:** As a user, I want to decrypt files using gesture passwords, so that I can access my protected data.

#### Acceptance Criteria

1. WHEN a user clicks a decrypt button for an encrypted file, THE File_Encryption_Manager SHALL open the Camera_Window for gesture password verification
2. WHEN a user completes gesture verification, THE File_Encryption_Manager SHALL compare the entered gesture password with the stored gesture password
3. IF the gesture passwords match, THEN THE File_Encryption_Manager SHALL derive the Encryption_Key and decrypt the file to the Original_Location
4. WHEN decryption completes successfully, THE File_Encryption_Manager SHALL delete the Encrypted_File
5. WHEN an Encrypted_File is deleted after decryption, THE File_Encryption_Manager SHALL remove the entry from the File_Registry
6. WHEN a File_Registry entry is removed, THE File_Encryption_Manager SHALL update the Main_Window to remove the file from display
7. IF the gesture passwords do not match, THEN THE File_Encryption_Manager SHALL display "Access Denied" message and retain the file in the list

### Requirement 3: File Removal

**User Story:** As a user, I want to remove files from the manager, so that I can clean up my encrypted file list.

#### Acceptance Criteria

1. WHEN a user requests to remove an encrypted file, THE File_Encryption_Manager SHALL display a dialog asking "Delete .enc file?" with options to delete or just remove from list
2. IF the user chooses to delete the file, THEN THE File_Encryption_Manager SHALL delete the Encrypted_File from disk and remove the entry from the File_Registry
3. IF the user chooses to remove from list only, THEN THE File_Encryption_Manager SHALL remove the entry from the File_Registry without deleting the Encrypted_File
4. WHEN a file is removed, THE File_Encryption_Manager SHALL update the Main_Window to remove the file from display

### Requirement 4: System File Protection

**User Story:** As a user, I want the system to prevent encryption of critical system files, so that I don't accidentally damage my operating system.

#### Acceptance Criteria

1. WHEN a user selects a file in a Windows system directory (C:\Windows, C:\Program Files, C:\Program Files (x86), System32), THE File_Encryption_Manager SHALL reject the file with an error message
2. WHEN a user selects a file with a system extension (.exe, .dll, .sys, .bat, .cmd, .ps1, .msi), THE File_Encryption_Manager SHALL reject the file with an error message
3. WHEN a user selects a hidden file, THE File_Encryption_Manager SHALL reject the file with an error message
4. WHEN a user selects an administrator-owned file, THE File_Encryption_Manager SHALL reject the file with an error message
5. WHEN a file is rejected, THE File_Encryption_Manager SHALL display an error message explaining why the file cannot be encrypted

### Requirement 5: File Size Limits

**User Story:** As a user, I want reasonable file size limits, so that encryption operations complete in acceptable time.

#### Acceptance Criteria

1. WHEN a user selects a file larger than 100MB, THE File_Encryption_Manager SHALL reject the file with an error message
2. WHEN a user selects a file of 100MB or smaller, THE File_Encryption_Manager SHALL proceed with encryption
3. THE File_Encryption_Manager SHALL support an unlimited number of encrypted files in the File_Registry

### Requirement 6: File Display

**User Story:** As a user, I want to see my encrypted files in a list, so that I can manage them easily.

#### Acceptance Criteria

1. THE Main_Window SHALL display a list of all encrypted files from the File_Registry
2. FOR EACH encrypted file, THE Main_Window SHALL display the file name and Original_Location
3. FOR EACH encrypted file, THE Main_Window SHALL display a decrypt button
4. WHEN the File_Registry is updated, THE Main_Window SHALL refresh the displayed file list

### Requirement 7: Missing File Handling

**User Story:** As a user, I want the system to handle missing encrypted files gracefully, so that I can maintain a clean file list.

#### Acceptance Criteria

1. WHEN a user attempts to decrypt a file, THE File_Encryption_Manager SHALL verify the Encrypted_File exists on disk
2. IF the Encrypted_File does not exist, THEN THE File_Encryption_Manager SHALL display an error message
3. WHEN an Encrypted_File is missing, THE File_Encryption_Manager SHALL remove the entry from the File_Registry
4. WHEN a missing file entry is removed, THE File_Encryption_Manager SHALL update the Main_Window to remove the file from display

### Requirement 8: File Naming

**User Story:** As a user, I want encrypted files to have clear naming, so that I can identify them easily.

#### Acceptance Criteria

1. WHEN a file is encrypted, THE File_Encryption_Manager SHALL append .enc extension to the original filename
2. WHEN a file is decrypted, THE File_Encryption_Manager SHALL restore the original filename by removing the .enc extension
3. IF a file with the original name exists at the Original_Location during decryption, THEN THE File_Encryption_Manager SHALL overwrite it

### Requirement 9: GUI Integration

**User Story:** As a user, I want a graphical interface for file management, so that I can easily interact with the system.

#### Acceptance Criteria

1. THE File_Encryption_Manager SHALL provide a Main_Window built with Tkinter
2. THE Main_Window SHALL provide an "Add File" button to initiate file encryption
3. WHEN gesture capture is needed, THE File_Encryption_Manager SHALL open the Camera_Window using OpenCV
4. WHEN gesture capture completes, THE File_Encryption_Manager SHALL close the Camera_Window and return to the Main_Window

### Requirement 10: Data Persistence

**User Story:** As a user, I want my encrypted file list to persist between sessions, so that I don't lose track of my files.

#### Acceptance Criteria

1. THE File_Encryption_Manager SHALL store all encrypted file metadata in encrypted_files.json
2. FOR EACH encrypted file, THE File_Registry SHALL store file ID, original path, encrypted path, gesture password, and file name
3. WHEN the File_Encryption_Manager starts, THE File_Encryption_Manager SHALL load the File_Registry from encrypted_files.json
4. WHEN the File_Registry is modified, THE File_Encryption_Manager SHALL save changes to encrypted_files.json
5. THE File_Registry SHALL store gesture passwords in plaintext format

### Requirement 11: Encryption Key Derivation

**User Story:** As a developer, I want secure key derivation from gesture passwords, so that the encryption is cryptographically sound.

#### Acceptance Criteria

1. WHEN a gesture password is captured, THE File_Encryption_Manager SHALL represent it as a 5-gesture sequence
2. WHEN deriving an Encryption_Key, THE File_Encryption_Manager SHALL convert the gesture password to a binary representation
3. WHEN a binary representation is created, THE File_Encryption_Manager SHALL compute the SHA-256 hash
4. WHEN the SHA-256 hash is computed, THE File_Encryption_Manager SHALL use the hash output as the AES-256 key
5. FOR ALL valid files, encrypting then decrypting with the same gesture password SHALL produce the original file contents (round-trip property)
