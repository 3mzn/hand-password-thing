# Gesture Lock 🔐

A production-ready hand gesture password system using **MediaPipe** and **OpenCV**.

Set a 3-gesture password using predefined hand gestures (based on which fingers are extended), then reproduce the same gestures to unlock. Uses binary finger state detection for fast, deterministic recognition.

## Quick Start

```bash
# 1. Activate the virtual environment
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Unix/macOS

# 2. Install dependencies (already done if you followed setup)
pip install -e .

# 3. Run the app
python -m src.main
```

## Controls

| Key | Action |
|-----|--------|
| `E` | Enroll a new 3-gesture password |
| `V` | Verify / unlock with your gestures |
| `R` | Reset everything |
| `Q` | Quit |

## How It Works

1. **Enroll**: Show 3 hand gestures (3 seconds each). The system detects which fingers are extended (up) or curled (down) for each gesture and stores the pattern.
2. **Verify**: Reproduce the same 3 gestures. The system compares your finger extension patterns against the enrolled ones using exact matching.
3. **Unlock**: If all 3 gestures match exactly → ACCESS GRANTED is displayed.

## Gesture Recognition

The system recognizes gestures based on **which fingers are extended**:

- **Fist**: All fingers curled (0 extended)
- **One**: Any single finger extended (e.g., thumbs up, pointing)
- **Two**: Any two fingers extended (e.g., peace sign, rock on)
- **Three**: Any three fingers extended
- **Four**: Any four fingers extended
- **Five**: All fingers extended (open palm)

Each gesture is represented as a 5-bit pattern: `[thumb, index, middle, ring, pinky]` where `True` = extended, `False` = curled.

### Real-Time Feedback

While capturing gestures, the UI displays:
- Which fingers are detected as extended (✓) or curled (✗)
- The current gesture class (Fist, One, Two, Three, Four, Five)
- A countdown timer showing time remaining

## Running Tests

```bash
python -m pytest tests/ -v
```

All 24 tests should pass, covering:
- Finger state detection (fist, open palm, peace sign, thumbs up)
- Gesture classification (Fist through Five)
- Pattern comparison (exact matching)
- Password store operations (enroll, verify, reset)

## Project Structure

```
src/
  config.py          # All tuneable constants
  capture.py         # Webcam + MediaPipe wrapper
  gesture.py         # Binary finger state detection & classification
  password_store.py  # In-memory password manager
  ui.py              # OpenCV overlay rendering
  main.py            # Entry point & state machine
tests/
  test_main.py       # Unit tests for gesture detection logic
```

## Technical Details

### Finger Detection
- **Regular Fingers** (index, middle, ring, pinky): Y-coordinate comparison - tip above knuckle by threshold = extended
- **Thumb**: X-coordinate distance from wrist - tip significantly farther in X-axis than base = extended
  - Threshold: 0.04 (4% of frame width)
  - Accounts for thumb's sideways extension motion

### Matching & Capture
- **Matching**: Exact boolean array equality (no fuzzy thresholds)
- **Capture**: Timer-based single-frame capture at end of countdown
- **Rotation Invariant**: Hand angle doesn't matter, only finger extension states
- **Fast**: Simple coordinate comparisons, no complex trigonometry or RMSE calculations

### Why X-Axis for Thumb?
The thumb extends **sideways** (horizontally) rather than up/down like other fingers. By measuring horizontal distance from the wrist, we can reliably detect when the thumb is extended outward vs. tucked into the palm.

## Dependencies

- Python 3.10+
- OpenCV (`opencv-python`)
- MediaPipe (`mediapipe`)
- NumPy (`numpy`)
- pytest (for testing)

## License

MIT
