# Design Document: Predefined Gesture Detection

## Overview

This design refactors the gesture lock system from a continuous feature-vector approach to a discrete predefined gesture recognition system. The current implementation extracts 24-dimensional feature vectors (joint angles, finger spreads, distances) and uses RMSE-based matching. The new system will:

1. Detect binary finger extension states (extended/curled) for each of five fingers
2. Classify gestures into six predefined categories based on extended finger count
3. Use timer-based single-frame capture instead of multi-sample averaging
4. Store and match gestures using exact boolean array equality

This approach simplifies the system, improves determinism, and makes gesture recognition more intuitive for users. The refactoring maintains the existing state machine and UI flow while replacing the core detection and matching logic.

### Key Design Decisions

**Binary State Detection**: Using simple coordinate comparisons (Y-axis for fingers, X-axis for thumb) provides robust, fast detection without complex trigonometry. This trades fine-grained gesture discrimination for reliability and speed.

**Predefined Classes**: Limiting gestures to six classes (Fist, One, Two, Three, Four, Five) based on extended finger count allows any finger combination within a class. This provides flexibility (e.g., "Two" can be index+middle or thumb+pinky) while maintaining simplicity.

**Timer-Based Capture**: Eliminating multi-sample averaging reduces complexity and latency. Users hold their gesture until the timer expires, then the system captures a single frame. This is more intuitive than maintaining a steady gesture across multiple samples.

**Exact Matching**: Boolean array equality replaces RMSE distance calculations, eliminating the need for threshold tuning and providing deterministic results.

## Architecture

### Component Overview

The system maintains the existing four-component architecture with modified responsibilities:

```
┌─────────────────┐
│   main.py       │  State machine orchestration
│                 │  (IDLE, ENROLLING, ENROLLED, VERIFYING, RESULT)
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼────┐ ┌─▼──────┐ ┌─▼────────┐ ┌▼─────────┐
│capture │ │gesture │ │password  │ │ui        │
│.py     │ │.py     │ │_store.py │ │.py       │
└────────┘ └────────┘ └──────────┘ └──────────┘
```

### Data Flow

**Enrollment Flow**:
```
Camera Frame → MediaPipe Landmarks → Finger State Detection → 
Gesture Pattern [bool×5] → Pattern Storage → Code Generation
```

**Verification Flow**:
```
Camera Frame → MediaPipe Landmarks → Finger State Detection → 
Gesture Pattern [bool×5] → Boolean Equality Check → Success/Failure
```

### Modified Components

**capture.py** (HandCapture):
- No changes to camera/MediaPipe integration
- Continues to return (21, 3) landmark arrays
- Timer logic remains in main.py state machine

**gesture.py** (GestureDetector):
- Remove: `_extract_features()`, `_safe_cos_angle()`, joint/spread angle calculations
- Remove: `average_landmarks()`, `compare()`, `compare_sequences()`
- Add: `detect_finger_states()` - binary extension detection
- Add: `classify_gesture()` - map finger count to gesture class
- Add: `compare_patterns()` - boolean array equality

**password_store.py** (PasswordStore):
- Change storage from `List[np.ndarray(24,)]` to `List[np.ndarray(5,) dtype=bool]`
- Replace `compare_sequences()` call with `compare_patterns()`
- Remove RMSE distance tracking

**ui.py** (UIRenderer):
- Add: `draw_finger_states()` - visualize current finger extension states
- Add: `draw_gesture_class()` - display current gesture class name
- Modify: `draw_status()` to show real-time finger state feedback

## Components and Interfaces

### GestureDetector (gesture.py)

#### Core Functions

```python
def detect_finger_states(landmarks: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect binary extension state for each finger.
    
    Args:
        landmarks: (21, 3) array of MediaPipe hand landmarks
        
    Returns:
        (5,) boolean array [thumb, index, middle, ring, pinky]
        or None if landmarks are invalid
        
    Algorithm:
        - Fingers (index, middle, ring, pinky): extended if tip.y < knuckle.y
        - Thumb: extended if |tip.x - knuckle.x| > EXTENSION_THRESHOLD_X
    """
```

```python
def classify_gesture(finger_states: np.ndarray) -> str:
    """
    Classify gesture based on extended finger count.
    
    Args:
        finger_states: (5,) boolean array
        
    Returns:
        One of: "Fist", "One", "Two", "Three", "Four", "Five"
        
    Algorithm:
        count = sum(finger_states)
        return ["Fist", "One", "Two", "Three", "Four", "Five"][count]
    """
```

```python
def compare_patterns(
    pattern1: np.ndarray,
    pattern2: np.ndarray
) -> bool:
    """
    Compare two gesture patterns for exact equality.
    
    Args:
        pattern1, pattern2: (5,) boolean arrays
        
    Returns:
        True if arrays are element-wise equal, False otherwise
    """
```

#### MediaPipe Landmark Mapping

```python
# Landmark indices (from MediaPipe Hands)
THUMB_TIP = 4
THUMB_KNUCKLE = 2  # CMC joint

FINGER_TIPS = [8, 12, 16, 20]      # index, middle, ring, pinky
FINGER_KNUCKLES = [5, 9, 13, 17]   # MCP joints
```

#### Configuration Constants

```python
# config.py additions
EXTENSION_THRESHOLD_X: float = 0.05  # Thumb extension threshold (normalized)
EXTENSION_THRESHOLD_Y: float = 0.0   # Finger extension threshold (unused, kept for clarity)

# config.py removals
# MATCH_THRESHOLD - no longer needed
# NUM_SAMPLES - no longer needed
```

### PasswordStore (password_store.py)

#### Modified Interface

```python
class PasswordStore:
    def __init__(self) -> None:
        self._enrolled: Optional[List[np.ndarray]] = None  # List of (5,) bool arrays
        self._code: Optional[str] = None
        
    def enroll(self, gestures: List[np.ndarray]) -> str:
        """
        Store gesture patterns and generate unlock code.
        
        Args:
            gestures: List of NUM_GESTURES (5,) boolean arrays
            
        Returns:
            5-digit unlock code string
        """
        
    def verify(self, candidates: List[np.ndarray]) -> tuple[bool, Optional[str]]:
        """
        Verify candidate patterns against enrolled patterns.
        
        Args:
            candidates: List of NUM_GESTURES (5,) boolean arrays
            
        Returns:
            (success, unlock_code_or_None)
            
        Note: No distance metrics returned - matching is binary
        """
```

### UIRenderer (ui.py)

#### New Functions

```python
def draw_finger_states(
    frame: np.ndarray,
    finger_states: Optional[np.ndarray],
    gesture_class: Optional[str]
) -> None:
    """
    Display real-time finger extension states and gesture class.
    
    Args:
        frame: BGR image to draw on
        finger_states: (5,) boolean array or None
        gesture_class: Gesture class name or None
        
    Visual Layout:
        Top-right corner:
        ┌─────────────────┐
        │ Thumb:  ✓       │
        │ Index:  ✓       │
        │ Middle: ✗       │
        │ Ring:   ✗       │
        │ Pinky:  ✗       │
        │                 │
        │ Class: Two      │
        └─────────────────┘
    """
```

### State Machine (main.py)

No structural changes to the state machine. Timer logic remains the same:

```python
# Existing timer-based capture (unchanged)
if state == State.ENROLLING:
    elapsed = time.time() - capture_start_time
    if elapsed >= CAPTURE_DURATION_SEC:
        # Capture single frame at timer expiration
        if result.landmarks is not None:
            pattern = detect_finger_states(result.landmarks)
            if pattern is not None:
                captured_gestures.append(pattern)
                # Continue to next gesture or complete enrollment
```

## Data Models

### Gesture Pattern

```python
# Type: np.ndarray with shape (5,) and dtype=bool
# Structure: [thumb, index, middle, ring, pinky]
# Values: True = extended, False = curled

# Example: Index and middle fingers extended (peace sign)
pattern = np.array([False, True, True, False, False], dtype=bool)
```

### Gesture Classes

```python
# Enumeration (implemented as string literals)
GESTURE_CLASSES = {
    0: "Fist",    # All fingers curled
    1: "One",     # Any single finger extended
    2: "Two",     # Any two fingers extended
    3: "Three",   # Any three fingers extended
    4: "Four",    # Any four fingers extended
    5: "Five"     # All fingers extended
}
```

### Landmark Coordinate System

MediaPipe provides normalized coordinates in [0, 1] range:
- X-axis: 0 (left) to 1 (right) in image space
- Y-axis: 0 (top) to 1 (bottom) in image space
- Z-axis: depth relative to wrist (not used in this design)

**Finger Extension Logic**:
- Fingers point upward when extended → tip.y < knuckle.y
- Thumb extends horizontally → |tip.x - knuckle.x| > threshold

### Storage Format

```python
# Enrolled password structure
enrolled_password: List[np.ndarray] = [
    np.array([False, True, False, False, False], dtype=bool),  # Gesture 1
    np.array([False, True, True, False, False], dtype=bool),   # Gesture 2
    np.array([True, True, True, True, True], dtype=bool)       # Gesture 3
]

# Serialization (if needed for future persistence)
# Convert to list of lists for JSON compatibility
serialized = [pattern.tolist() for pattern in enrolled_password]
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Finger Extension Detection

*For any* valid MediaPipe landmarks where a finger's (index, middle, ring, or pinky) fingertip Y-coordinate is less than its knuckle Y-coordinate, the corresponding finger state SHALL be marked as extended (True), and for any finger where the fingertip Y-coordinate is greater than or equal to the knuckle Y-coordinate, the finger state SHALL be marked as curled (False).

**Validates: Requirements 1.2, 1.3**

### Property 2: Thumb Extension Detection

*For any* valid MediaPipe landmarks where the thumb fingertip X-coordinate distance from the thumb knuckle exceeds EXTENSION_THRESHOLD_X, the thumb state SHALL be marked as extended (True), and for any thumb where the X-coordinate distance is less than or equal to EXTENSION_THRESHOLD_X, the thumb state SHALL be marked as curled (False).

**Validates: Requirements 1.4, 1.5**

### Property 3: Gesture Pattern Structure

*For any* valid MediaPipe landmarks, the detect_finger_states function SHALL return a 5-element boolean array in the order [thumb, index, middle, ring, pinky], where each element represents the extension state of the corresponding finger.

**Validates: Requirements 1.1, 1.6**

### Property 4: Gesture Classification by Count

*For any* gesture pattern (5-element boolean array), the classify_gesture function SHALL return a class name that depends only on the count of extended fingers (sum of True values), such that patterns with the same count receive the same classification regardless of which specific fingers are extended.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7**

### Property 5: Pattern Storage Round-Trip

*For any* sequence of NUM_GESTURES gesture patterns, enrolling the sequence in the PasswordStore and then immediately verifying with the same sequence SHALL result in successful verification with the unlock code returned.

**Validates: Requirements 4.1, 4.2, 4.4**

### Property 6: Pattern Equality Verification

*For any* two gesture patterns, the compare_patterns function SHALL return True if and only if the patterns are element-wise equal (all five boolean values match), and SHALL return False for any patterns that differ in at least one position.

**Validates: Requirements 4.4**

### Property 7: Invalid Landmark Handling

*For any* invalid landmark data (wrong shape, NaN values, or None), the detect_finger_states function SHALL return None and log an error without raising an exception.

**Validates: Requirements 10.2**

### Property 8: Function Purity

*For any* valid MediaPipe landmarks, calling detect_finger_states multiple times with the same input SHALL produce identical output, demonstrating that the function maintains no state between invocations.

**Validates: Requirements 12.2**

### Property 9: Unlock Code Format

*For any* successful enrollment, the generated unlock code SHALL be a string of exactly 5 decimal digits (matching the pattern "\\d{5}").

**Validates: Requirements 8.4**

### Property 10: Rotation Invariance

*For any* valid MediaPipe landmarks, if the relative Y-coordinate relationships between fingertips and knuckles are preserved (for fingers) and the X-coordinate distance is preserved (for thumb), then rotating or translating the entire hand SHALL produce the same gesture pattern.

**Validates: Requirements 7.1**

## Error Handling

### Input Validation

**Landmark Validation**:
- Check landmarks shape is (21, 3) before processing
- Verify all coordinate values are finite (not NaN or Inf)
- Return None for invalid inputs rather than raising exceptions
- Log warnings for invalid data to aid debugging

**Pattern Validation**:
- Verify gesture patterns are (5,) boolean arrays before storage
- Check sequence length matches NUM_GESTURES during enrollment/verification
- Raise ValueError with descriptive messages for invalid sequences

### Runtime Error Handling

**Camera Failures**:
- HandCapture.open() raises RuntimeError if camera cannot be opened
- HandCapture.get_frame() raises RuntimeError if frame read fails
- Main loop catches exceptions and displays error messages to user
- User can press 'R' to reset and retry

**MediaPipe Failures**:
- If MediaPipe returns no landmarks, treat as "hand not detected"
- Display real-time feedback: "Hand not detected" message
- At timer expiration, if no hand detected, restart timer and show warning
- Never crash on missing hand detection—this is expected during normal use

**State Machine Errors**:
- PasswordStore.verify() raises RuntimeError if called before enrollment
- This should never happen in normal flow (UI prevents it)
- If it occurs, log error and return to IDLE state

### Edge Cases

**Boundary Conditions**:
- Fingertip Y-coordinate exactly equal to knuckle Y-coordinate → classify as curled (>=)
- Thumb X-distance exactly equal to threshold → classify as curled (<=)
- Zero fingers extended → classify as "Fist" (edge case, but valid)
- All five fingers extended → classify as "Five" (edge case, but valid)

**Ambiguous Hand Positions**:
- Partially curled fingers near the threshold → accept the binary decision
- Hand at extreme angles → rely on MediaPipe landmark quality
- Multiple hands in frame → MediaPipe returns only one (max_num_hands=1)

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Specific gesture examples (fist, peace sign, thumbs up, open palm)
- Edge cases (zero fingers, all fingers, boundary coordinates)
- Error conditions (invalid landmarks, None inputs, wrong shapes)
- Integration tests for state machine transitions
- UI rendering function calls (verify correct data passed)

**Property-Based Tests**: Verify universal properties across all inputs
- Use Hypothesis library for Python property-based testing
- Generate random landmark coordinates within valid ranges
- Generate random gesture patterns for classification testing
- Each property test runs minimum 100 iterations
- Property tests catch edge cases that unit tests might miss

### Property-Based Testing Configuration

**Library**: Hypothesis (https://hypothesis.readthedocs.io/)

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(landmarks=st_valid_landmarks())
def test_property_X(landmarks):
    # Test implementation
    pass
```

**Custom Strategies**:
```python
# Strategy for generating valid MediaPipe landmarks
@st.composite
def st_valid_landmarks(draw):
    # Generate (21, 3) array with coordinates in [0, 1] range
    return draw(st.arrays(
        dtype=np.float64,
        shape=(21, 3),
        elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
    ))

# Strategy for generating gesture patterns
@st.composite
def st_gesture_pattern(draw):
    # Generate (5,) boolean array
    return draw(st.arrays(
        dtype=bool,
        shape=(5,),
        elements=st.booleans()
    ))
```

**Test Tagging**:
Each property-based test must include a comment referencing the design property:

```python
def test_finger_extension_detection():
    """
    Feature: predefined-gesture-detection, Property 1:
    For any valid MediaPipe landmarks where a finger's fingertip Y-coordinate
    is less than its knuckle Y-coordinate, the finger state SHALL be extended.
    """
    # Test implementation
```

### Test Coverage Requirements

**Unit Test Coverage**:
- `test_detect_finger_states_fist()` - all fingers curled
- `test_detect_finger_states_open_palm()` - all fingers extended
- `test_detect_finger_states_peace_sign()` - index and middle extended
- `test_detect_finger_states_thumbs_up()` - only thumb extended
- `test_detect_finger_states_invalid_shape()` - wrong landmark shape
- `test_detect_finger_states_none_input()` - None input
- `test_classify_gesture_all_classes()` - test each class (Fist through Five)
- `test_compare_patterns_equal()` - identical patterns match
- `test_compare_patterns_different()` - different patterns don't match
- `test_password_store_enroll_verify_success()` - round-trip success
- `test_password_store_verify_failure()` - wrong patterns fail
- `test_unlock_code_format()` - code is 5 digits

**Property-Based Test Coverage**:
- `test_property_finger_extension()` - Property 1
- `test_property_thumb_extension()` - Property 2
- `test_property_pattern_structure()` - Property 3
- `test_property_classification_by_count()` - Property 4
- `test_property_storage_round_trip()` - Property 5
- `test_property_pattern_equality()` - Property 6
- `test_property_invalid_handling()` - Property 7
- `test_property_function_purity()` - Property 8
- `test_property_unlock_code_format()` - Property 9
- `test_property_rotation_invariance()` - Property 10

### Integration Testing

**State Machine Testing**:
- Test full enrollment flow (IDLE → ENROLLING → ENROLLED)
- Test full verification flow (ENROLLED → VERIFYING → RESULT)
- Test reset functionality (any state → IDLE)
- Test keyboard shortcuts (E, V, R, Q)
- Test timer expiration behavior
- Test hand detection failure handling

**End-to-End Testing**:
- Manual testing with real webcam and hand gestures
- Verify UI displays correct finger states in real-time
- Verify timer countdown displays correctly
- Verify gesture capture at timer expiration
- Verify unlock code display on successful verification
- Test with different hand sizes, angles, and lighting conditions

### Performance Testing

**Benchmarks**:
- Measure `detect_finger_states()` execution time (target: <10ms)
- Measure `compare_patterns()` execution time (target: <1ms)
- Measure frame processing rate (target: 30 FPS)
- Profile memory usage during enrollment and verification

**Performance Test Implementation**:
```python
import time

def test_finger_detection_performance():
    landmarks = generate_test_landmarks()
    iterations = 1000
    
    start = time.perf_counter()
    for _ in range(iterations):
        detect_finger_states(landmarks)
    end = time.perf_counter()
    
    avg_time_ms = (end - start) / iterations * 1000
    assert avg_time_ms < 10, f"Detection too slow: {avg_time_ms:.2f}ms"
```

### Test Execution

**Running Tests**:
```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/ -m "not property"

# Run only property-based tests
pytest tests/ -m property

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run performance benchmarks
pytest tests/test_performance.py -v
```

**Continuous Integration**:
- All tests must pass before merging
- Property-based tests run with 100 examples in CI
- Coverage target: >90% for gesture.py and password_store.py
- Performance benchmarks run on dedicated hardware for consistency
