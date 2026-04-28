# Requirements Document

## Introduction

This document specifies requirements for refactoring the gesture lock system from storing arbitrary hand shapes (24-dimensional feature vectors) to recognizing predefined gestures based on binary finger extension states. The new system will detect which fingers are extended or curled, classify gestures into predefined categories, and use timer-based capture instead of sample averaging.

## Glossary

- **Gesture_Detector**: The component responsible for analyzing hand landmarks and determining finger extension states
- **Finger_State**: Binary state (extended or curled) for a single finger
- **Gesture_Pattern**: A 5-bit boolean array representing the extension state of all five fingers [thumb, index, middle, ring, pinky]
- **Gesture_Class**: A category of gestures based on the count of extended fingers (Fist, One, Two, Three, Four, Five)
- **Password_Store**: The component that stores and verifies enrolled gesture patterns
- **Capture_System**: The component that manages the timer-based gesture capture process
- **Extension_Threshold**: The Y-coordinate difference threshold used to determine if a finger is extended
- **Fingertip**: MediaPipe landmark representing the tip of a finger
- **Knuckle**: MediaPipe landmark representing the base joint of a finger (MCP for fingers, CMC for thumb)
- **UI_Renderer**: The component that displays visual feedback to the user

## Requirements

### Requirement 1: Binary Finger State Detection

**User Story:** As a user, I want the system to detect whether each finger is extended or curled, so that gesture recognition is simple and deterministic.

#### Acceptance Criteria

1. THE Gesture_Detector SHALL determine the Finger_State for each of the five fingers: thumb, index, middle, ring, and pinky
2. FOR each finger except the thumb, WHEN the Fingertip Y-coordinate is less than the Knuckle Y-coordinate, THE Gesture_Detector SHALL classify the Finger_State as extended
3. FOR each finger except the thumb, WHEN the Fingertip Y-coordinate is greater than or equal to the Knuckle Y-coordinate, THE Gesture_Detector SHALL classify the Finger_State as curled
4. FOR the thumb, WHEN the Fingertip X-coordinate distance from the Knuckle exceeds the Extension_Threshold, THE Gesture_Detector SHALL classify the Finger_State as extended
5. FOR the thumb, WHEN the Fingertip X-coordinate distance from the Knuckle is less than or equal to the Extension_Threshold, THE Gesture_Detector SHALL classify the Finger_State as curled
6. THE Gesture_Detector SHALL output a Gesture_Pattern as a 5-element boolean array in the order [thumb, index, middle, ring, pinky]

### Requirement 2: Predefined Gesture Classification

**User Story:** As a user, I want the system to recognize gestures based on how many fingers are extended, so that I can use intuitive hand shapes as passwords.

#### Acceptance Criteria

1. WHEN zero fingers are extended, THE Gesture_Detector SHALL classify the gesture as "Fist"
2. WHEN exactly one finger is extended, THE Gesture_Detector SHALL classify the gesture as "One"
3. WHEN exactly two fingers are extended, THE Gesture_Detector SHALL classify the gesture as "Two"
4. WHEN exactly three fingers are extended, THE Gesture_Detector SHALL classify the gesture as "Three"
5. WHEN exactly four fingers are extended, THE Gesture_Detector SHALL classify the gesture as "Four"
6. WHEN all five fingers are extended, THE Gesture_Detector SHALL classify the gesture as "Five"
7. THE Gesture_Detector SHALL recognize ANY combination of extended fingers within each Gesture_Class (e.g., index+middle or thumb+pinky both classify as "Two")

### Requirement 3: Timer-Based Capture

**User Story:** As a user, I want the system to capture my gesture state at the end of a timer, so that I don't need to hold the gesture perfectly steady for multiple samples.

#### Acceptance Criteria

1. WHEN the user initiates gesture capture, THE Capture_System SHALL start a countdown timer
2. WHILE the timer is running, THE UI_Renderer SHALL display the remaining time to the user
3. WHEN the timer expires, THE Capture_System SHALL capture the current hand landmarks exactly once
4. WHEN the timer expires, THE Gesture_Detector SHALL process the captured landmarks and extract the Gesture_Pattern
5. THE Capture_System SHALL NOT average multiple samples during a single gesture capture
6. WHEN no hand is detected at timer expiration, THE Capture_System SHALL display an error message and restart the timer

### Requirement 4: Gesture Pattern Storage

**User Story:** As a developer, I want the system to store gesture patterns as 5-bit boolean arrays, so that storage is efficient and matching is exact.

#### Acceptance Criteria

1. WHEN a user enrolls a password, THE Password_Store SHALL store each Gesture_Pattern as a 5-element boolean array
2. THE Password_Store SHALL store a sequence of Gesture_Patterns equal to NUM_GESTURES (currently 3)
3. THE Password_Store SHALL NOT store 24-dimensional feature vectors
4. WHEN verifying a password, THE Password_Store SHALL compare Gesture_Patterns using exact boolean array equality
5. THE Password_Store SHALL NOT use RMSE distance calculations for pattern matching

### Requirement 5: Visual Feedback for Finger States

**User Story:** As a user, I want to see which fingers the system detects as extended or curled, so that I can adjust my hand position if needed.

#### Acceptance Criteria

1. WHILE a hand is detected, THE UI_Renderer SHALL display the current Gesture_Pattern on screen
2. FOR each finger, THE UI_Renderer SHALL indicate whether the Finger_State is extended or curled
3. THE UI_Renderer SHALL display the current Gesture_Class name (Fist, One, Two, Three, Four, Five)
4. THE UI_Renderer SHALL update the finger state display in real-time as the hand moves
5. WHEN the timer expires during capture, THE UI_Renderer SHALL highlight the captured Gesture_Pattern

### Requirement 6: Configuration Parameters

**User Story:** As a developer, I want configurable thresholds for finger extension detection, so that the system can be tuned for different hand sizes and camera angles.

#### Acceptance Criteria

1. THE Gesture_Detector SHALL use a configurable Extension_Threshold value from the configuration module
2. THE configuration module SHALL define EXTENSION_THRESHOLD_Y for vertical finger extension detection
3. THE configuration module SHALL define EXTENSION_THRESHOLD_X for thumb extension detection
4. THE configuration module SHALL remove MATCH_THRESHOLD as it is no longer used
5. THE configuration module SHALL remove NUM_SAMPLES as sample averaging is no longer used

### Requirement 7: Rotation Invariance

**User Story:** As a user, I want the system to recognize my gestures regardless of hand rotation, so that I don't need to hold my hand at a specific angle.

#### Acceptance Criteria

1. THE Gesture_Detector SHALL determine Finger_State based only on fingertip and knuckle positions
2. THE Gesture_Detector SHALL NOT use hand angle or rotation in Finger_State determination
3. THE Gesture_Detector SHALL NOT use inter-finger spread angles in Finger_State determination
4. THE Gesture_Detector SHALL NOT use wrist position in Finger_State determination

### Requirement 8: Backward Compatibility for Capture Flow

**User Story:** As a user, I want the enrollment and verification flow to remain familiar, so that I can use the system without relearning the interface.

#### Acceptance Criteria

1. THE Capture_System SHALL maintain the same keyboard shortcuts (E for enroll, V for verify, R for reset, Q for quit)
2. THE Capture_System SHALL maintain the same state machine (IDLE, ENROLLING, ENROLLED, VERIFYING, RESULT)
3. THE Capture_System SHALL maintain the same NUM_GESTURES configuration (default 3 gestures per password)
4. WHEN enrollment completes, THE Password_Store SHALL generate a 5-digit unlock code
5. WHEN verification succeeds, THE Capture_System SHALL display the unlock code

### Requirement 9: MediaPipe Landmark Mapping

**User Story:** As a developer, I want clear mapping between MediaPipe landmarks and finger detection, so that the implementation is maintainable.

#### Acceptance Criteria

1. THE Gesture_Detector SHALL use MediaPipe landmark index 4 for the thumb Fingertip
2. THE Gesture_Detector SHALL use MediaPipe landmark index 2 for the thumb Knuckle
3. THE Gesture_Detector SHALL use MediaPipe landmark indices [8, 12, 16, 20] for the Fingertips of index, middle, ring, and pinky respectively
4. THE Gesture_Detector SHALL use MediaPipe landmark indices [5, 9, 13, 17] for the Knuckles of index, middle, ring, and pinky respectively
5. THE Gesture_Detector SHALL document the landmark mapping in code comments

### Requirement 10: Error Handling for Edge Cases

**User Story:** As a user, I want clear feedback when the system cannot detect my hand or fingers, so that I know what to adjust.

#### Acceptance Criteria

1. WHEN no hand landmarks are detected, THE Gesture_Detector SHALL return None for the Gesture_Pattern
2. WHEN MediaPipe provides invalid landmark data, THE Gesture_Detector SHALL log an error and return None
3. WHEN a Gesture_Pattern is None during capture, THE Capture_System SHALL display a warning message
4. WHEN a Gesture_Pattern is None at timer expiration, THE Capture_System SHALL restart the capture timer
5. THE UI_Renderer SHALL display "Hand not detected" when the Gesture_Pattern is None

### Requirement 11: Test Coverage for New Detection Logic

**User Story:** As a developer, I want comprehensive tests for finger state detection, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. THE test suite SHALL include tests for all five Gesture_Class categories (Fist, One, Two, Three, Four, Five)
2. THE test suite SHALL include tests for thumb extension detection using X-coordinate differences
3. THE test suite SHALL include tests for finger extension detection using Y-coordinate differences
4. THE test suite SHALL include tests for edge cases where fingertip and knuckle coordinates are equal
5. THE test suite SHALL include tests verifying that Gesture_Pattern matching uses exact boolean equality
6. THE test suite SHALL include tests for various finger combinations within each Gesture_Class

### Requirement 12: Performance Requirements

**User Story:** As a user, I want gesture detection to be fast and responsive, so that the system feels natural to use.

#### Acceptance Criteria

1. WHEN processing a single frame, THE Gesture_Detector SHALL complete Finger_State detection within 10 milliseconds
2. THE Gesture_Detector SHALL process each frame independently without maintaining state between frames
3. THE Gesture_Detector SHALL NOT perform complex mathematical operations such as cosine calculations or RMSE
4. WHEN comparing two Gesture_Patterns, THE Password_Store SHALL complete the comparison within 1 millisecond

### Requirement 13: Code Removal and Cleanup

**User Story:** As a developer, I want obsolete code removed, so that the codebase remains maintainable and clear.

#### Acceptance Criteria

1. THE Gesture_Detector SHALL NOT include functions for computing joint bend angles
2. THE Gesture_Detector SHALL NOT include functions for computing inter-finger spread angles
3. THE Gesture_Detector SHALL NOT include functions for computing fingertip-to-wrist distances
4. THE Gesture_Detector SHALL NOT include the _extract_features function
5. THE Gesture_Detector SHALL NOT include the average_landmarks function for multi-sample averaging
6. THE configuration module SHALL NOT include MATCH_THRESHOLD constant
7. THE configuration module SHALL NOT include NUM_SAMPLES constant
