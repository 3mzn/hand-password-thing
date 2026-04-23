# Implementation Plan: Predefined Gesture Detection

## Overview

This implementation refactors the gesture lock system from continuous feature-vector matching (24-dim RMSE-based) to discrete predefined gesture recognition. The approach maintains the existing state machine and UI flow while replacing core detection and matching logic with binary finger state detection, predefined gesture classification, timer-based single-frame capture, and exact boolean pattern matching.

## Tasks

- [x] 1. Update configuration and remove obsolete constants
  - Remove MATCH_THRESHOLD and NUM_SAMPLES from config.py
  - Add EXTENSION_THRESHOLD_X (default: 0.05) for thumb extension detection
  - Add EXTENSION_THRESHOLD_Y (default: 0.0) for finger extension detection (kept for clarity)
  - Document the new thresholds with comments explaining their purpose
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2. Implement core finger state detection in gesture.py
  - [x] 2.1 Create detect_finger_states() function
    - Accept (21, 3) landmark array as input
    - Validate landmark shape and check for NaN/Inf values
    - Implement Y-coordinate comparison for fingers (tip.y < knuckle.y = extended)
    - Implement X-coordinate distance check for thumb (|tip.x - knuckle.x| > EXTENSION_THRESHOLD_X = extended)
    - Return (5,) boolean array [thumb, index, middle, ring, pinky] or None for invalid input
    - Use MediaPipe landmark indices: thumb (4, 2), fingers ([8,12,16,20], [5,9,13,17])
    - Add docstring documenting the landmark mapping
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2_
  
  - [ ]* 2.2 Write property test for finger extension detection
    - **Property 1: Finger Extension Detection**
    - **Validates: Requirements 1.2, 1.3**
    - Generate random valid landmarks with Hypothesis
    - Verify fingers with tip.y < knuckle.y are marked extended
    - Verify fingers with tip.y >= knuckle.y are marked curled
  
  - [ ]* 2.3 Write property test for thumb extension detection
    - **Property 2: Thumb Extension Detection**
    - **Validates: Requirements 1.4, 1.5**
    - Generate random valid landmarks with Hypothesis
    - Verify thumb with |tip.x - knuckle.x| > threshold is marked extended
    - Verify thumb with |tip.x - knuckle.x| <= threshold is marked curled
  
  - [ ]* 2.4 Write property test for pattern structure
    - **Property 3: Gesture Pattern Structure**
    - **Validates: Requirements 1.1, 1.6**
    - Generate random valid landmarks
    - Verify output is (5,) boolean array in order [thumb, index, middle, ring, pinky]
    - Verify function returns None for invalid inputs

- [x] 3. Implement gesture classification in gesture.py
  - [x] 3.1 Create classify_gesture() function
    - Accept (5,) boolean array as input
    - Count extended fingers (sum of True values)
    - Return gesture class name: "Fist" (0), "One" (1), "Two" (2), "Three" (3), "Four" (4), "Five" (5)
    - Add docstring explaining the classification logic
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [ ]* 3.2 Write property test for classification by count
    - **Property 4: Gesture Classification by Count**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7**
    - Generate random gesture patterns with Hypothesis
    - Verify patterns with same extended finger count receive same classification
    - Verify all six classes are correctly mapped (0-5 extended fingers)
  
  - [ ]* 3.3 Write unit tests for all gesture classes
    - Test "Fist" (all False)
    - Test "One" (one True, various positions)
    - Test "Two" (two True, various combinations)
    - Test "Three" (three True, various combinations)
    - Test "Four" (four True, various positions)
    - Test "Five" (all True)
    - _Requirements: 11.1_

- [x] 4. Implement pattern comparison in gesture.py
  - [x] 4.1 Create compare_patterns() function
    - Accept two (5,) boolean arrays as input
    - Return True if arrays are element-wise equal, False otherwise
    - Use numpy array_equal or equivalent for comparison
    - Add docstring explaining exact equality matching
    - _Requirements: 4.4, 4.5_
  
  - [ ]* 4.2 Write property test for pattern equality
    - **Property 6: Pattern Equality Verification**
    - **Validates: Requirements 4.4**
    - Generate random gesture patterns with Hypothesis
    - Verify identical patterns return True
    - Verify patterns differing in at least one position return False
    - Test all possible single-bit differences

- [x] 5. Remove obsolete functions from gesture.py
  - Remove _safe_cos_angle() function
  - Remove _extract_features() function
  - Remove _JOINT_TRIPLETS, _TIPS, _SPREAD_PAIRS constants
  - Remove normalise() function (replaced by detect_finger_states)
  - Remove average_landmarks() function (no longer needed)
  - Remove compare() function (replaced by compare_patterns)
  - Remove compare_sequences() function (will be replaced in PasswordStore)
  - Clean up imports (remove unused numpy operations if any)
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 6. Checkpoint - Verify gesture.py refactoring
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update PasswordStore to use boolean patterns
  - [x] 7.1 Modify PasswordStore._enrolled type annotation
    - Change from List[np.ndarray] (24,) to List[np.ndarray] (5,) dtype=bool
    - Update docstrings to reflect new storage format
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 7.2 Update PasswordStore.enroll() method
    - Validate input gestures are (5,) boolean arrays
    - Store gestures as boolean arrays (no feature vector conversion)
    - Keep unlock code generation logic unchanged
    - _Requirements: 4.1, 4.2, 8.4_
  
  - [x] 7.3 Update PasswordStore.verify() method
    - Replace compare_sequences() call with element-wise compare_patterns() calls
    - Remove distance tracking (no RMSE calculations)
    - Return (success, unlock_code_or_None) instead of (success, distances, code)
    - Update docstring to reflect new return signature
    - _Requirements: 4.4, 4.5_
  
  - [ ]* 7.4 Write property test for storage round-trip
    - **Property 5: Pattern Storage Round-Trip**
    - **Validates: Requirements 4.1, 4.2, 4.4**
    - Generate random gesture sequences with Hypothesis
    - Enroll sequence and immediately verify with same sequence
    - Verify verification succeeds and returns unlock code
  
  - [ ]* 7.5 Write unit tests for PasswordStore
    - Test enroll with valid patterns
    - Test verify success with matching patterns
    - Test verify failure with non-matching patterns
    - Test unlock code format (5 digits)
    - Test error handling (verify before enroll, wrong sequence length)
    - _Requirements: 11.5_

- [x] 8. Update main.py to use timer-based single-frame capture
  - [x] 8.1 Modify _handle_capture() to capture single frame at timer expiration
    - Remove sample_buffer and NUM_SAMPLES logic
    - Remove sample interval calculations
    - At timer expiration, call detect_finger_states() once on current landmarks
    - If landmarks is None at expiration, restart timer and show error
    - Store resulting (5,) boolean pattern directly in gesture_buffer
    - Update status messages to remove sample count display
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [x] 8.2 Update imports in main.py
    - Remove import of normalise and average_landmarks from gesture module
    - Add import of detect_finger_states from gesture module
    - Remove NUM_SAMPLES from config imports
    - _Requirements: 3.5_
  
  - [x] 8.3 Update _finish_capture() to handle new return signature
    - Update verify() call to expect (success, code) instead of (success, distances, code)
    - Remove _result_distances field from GestureLockApp
    - Update result screen call to not pass distances
    - _Requirements: 4.5_

- [x] 9. Add real-time finger state UI feedback
  - [x] 9.1 Create draw_finger_states() function in ui.py
    - Accept frame, finger_states (5,) boolean array or None, gesture_class string or None
    - Display finger states in top-right corner with checkmarks (✓) for extended, crosses (✗) for curled
    - Display labels: "Thumb", "Index", "Middle", "Ring", "Pinky"
    - Display current gesture class name below finger states
    - Handle None inputs gracefully (show "Hand not detected")
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 10.5_
  
  - [x] 9.2 Integrate draw_finger_states() into main.py
    - In _handle_capture(), call detect_finger_states() on current landmarks
    - Call classify_gesture() on resulting pattern
    - Call draw_finger_states() with pattern and class name
    - Update display in real-time as hand moves
    - Highlight captured pattern when timer expires
    - _Requirements: 5.4, 5.5_

- [x] 10. Update draw_result_screen() in ui.py
  - Remove distances parameter from function signature
  - Remove distance display from result screen
  - Keep success/failure message and unlock code display
  - Simplify result screen to show only verification outcome
  - _Requirements: 4.5_

- [x] 11. Checkpoint - Verify integration and UI updates
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Write comprehensive unit tests
  - [ ]* 12.1 Write unit tests for detect_finger_states()
    - Test fist gesture (all fingers curled)
    - Test open palm (all fingers extended)
    - Test peace sign (index and middle extended)
    - Test thumbs up (only thumb extended)
    - Test invalid shape input
    - Test None input
    - Test NaN/Inf values in landmarks
    - _Requirements: 11.2, 11.3, 11.4_
  
  - [ ]* 12.2 Write unit tests for classify_gesture()
    - Test all six gesture classes with various finger combinations
    - Verify "Two" works for index+middle, thumb+pinky, etc.
    - _Requirements: 11.1, 11.6_
  
  - [ ]* 12.3 Write unit tests for compare_patterns()
    - Test identical patterns return True
    - Test different patterns return False
    - Test edge cases (all True, all False)
    - _Requirements: 11.5_

- [x] 13. Write property-based tests
  - [ ]* 13.1 Write property test for invalid landmark handling
    - **Property 7: Invalid Landmark Handling**
    - **Validates: Requirements 10.2**
    - Generate invalid landmarks (wrong shape, NaN, None)
    - Verify detect_finger_states returns None without raising exceptions
  
  - [ ]* 13.2 Write property test for function purity
    - **Property 8: Function Purity**
    - **Validates: Requirements 12.2**
    - Generate random valid landmarks
    - Call detect_finger_states multiple times with same input
    - Verify all outputs are identical
  
  - [ ]* 13.3 Write property test for unlock code format
    - **Property 9: Unlock Code Format**
    - **Validates: Requirements 8.4**
    - Generate random gesture sequences
    - Enroll and verify unlock code matches pattern "\\d{5}"
  
  - [ ]* 13.4 Write property test for rotation invariance
    - **Property 10: Rotation Invariance**
    - **Validates: Requirements 7.1**
    - Generate landmarks with preserved Y-coordinate relationships
    - Apply translations and verify same gesture pattern results
    - Note: Full rotation testing requires coordinate transformations

- [x] 14. Performance testing and optimization
  - [ ]* 14.1 Write performance benchmark for detect_finger_states()
    - Measure execution time over 1000 iterations
    - Verify average time < 10ms per call
    - _Requirements: 12.1_
  
  - [ ]* 14.2 Write performance benchmark for compare_patterns()
    - Measure execution time over 10000 iterations
    - Verify average time < 1ms per call
    - _Requirements: 12.4_

- [x] 15. Final integration testing and cleanup
  - [x] 15.1 Manual end-to-end testing
    - Test enrollment flow with real webcam
    - Test verification flow with matching gestures
    - Test verification flow with non-matching gestures
    - Verify real-time finger state display updates correctly
    - Verify timer countdown works as expected
    - Test error handling (no hand detected at timer expiration)
    - Test all keyboard shortcuts (E, V, R, Q)
  
  - [x] 15.2 Code cleanup and documentation
    - Add module-level docstring to gesture.py explaining new approach
    - Update comments in main.py to reflect timer-based capture
    - Remove any commented-out old code
    - Verify all functions have proper docstrings
    - Run linter and fix any issues

- [x] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across random inputs
- Unit tests validate specific examples, edge cases, and integration points
- The refactoring maintains backward compatibility for the state machine and UI flow
- Timer-based capture eliminates multi-sample averaging complexity
- Binary finger state detection is simpler and faster than 24-dim feature extraction
