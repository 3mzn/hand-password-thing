"""
Gesture Lock — Main entry point and state machine.

States:
    IDLE       →  Show instructions; press E to enroll, V to verify
    ENROLLING  →  Capture NUM_GESTURES gestures (CAPTURE_DURATION_SEC each)
    ENROLLED   →  Password set; press V to verify
    VERIFYING  →  Capture and compare against enrolled gestures
    RESULT     →  Show unlock code or denial; press R to reset
"""

from __future__ import annotations

import enum
import logging
import os
import sys
import time
from typing import List, Optional

import cv2
import numpy as np

# Add the parent directory to sys.path if run directly as a script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.capture import HandCapture
    from src.config import (
        CAPTURE_DURATION_SEC,
        COLOR_BLUE,
        COLOR_GREEN,
        COLOR_RED,
        COLOR_YELLOW,
        NUM_GESTURES,
        WINDOW_NAME,
    )
    from src.gesture import classify_gesture, detect_finger_states
    from src.password_store import PasswordStore
    from src.ui import (
        draw_enrolled_screen,
        draw_finger_states,
        draw_gesture_index,
        draw_hand_missing_warning,
        draw_idle_screen,
        draw_progress_bar,
        draw_result_screen,
        draw_status,
    )
except ImportError:
    # Fallback for direct execution if the above fails
    from capture import HandCapture
    from config import (
        CAPTURE_DURATION_SEC,
        COLOR_BLUE,
        COLOR_GREEN,
        COLOR_RED,
        COLOR_YELLOW,
        NUM_GESTURES,
        WINDOW_NAME,
    )
    from gesture import classify_gesture, detect_finger_states
    from password_store import PasswordStore
    from ui import (
        draw_enrolled_screen,
        draw_finger_states,
        draw_gesture_index,
        draw_hand_missing_warning,
        draw_idle_screen,
        draw_progress_bar,
        draw_result_screen,
        draw_status,
    )

# ── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── State machine ───────────────────────────────────────────────────

class State(enum.Enum):
    IDLE = "idle"
    ENROLLING = "enrolling"
    ENROLLED = "enrolled"
    VERIFYING = "verifying"
    RESULT = "result"


class GestureLockApp:
    """Top-level application controller."""

    def __init__(self) -> None:
        self._capture = HandCapture()
        self._store = PasswordStore()
        self._state = State.IDLE

        # capture session state
        self._gesture_buffer: List[np.ndarray] = []      # collected gesture patterns (5,) bool arrays
        self._capture_start: float = 0.0
        self._current_gesture_idx: int = 0

        # result state
        self._result_success: bool = False

        # countdown / pre-capture
        self._pre_countdown_start: float = 0.0
        self._pre_countdown_active: bool = False
        self._PRE_COUNTDOWN_SEC: float = 1.5  # brief pause between gestures

    # ── main loop ───────────────────────────────────────────────────

    def run(self) -> None:
        """Open camera and enter the main event loop."""
        try:
            with self._capture:
                logger.info("Application started. Press Q to quit.")
                while True:
                    frame_result = self._capture.get_frame()
                    frame = frame_result.frame
                    landmarks = frame_result.landmarks

                    # Dispatch to state handler
                    handler = {
                        State.IDLE: self._handle_idle,
                        State.ENROLLING: self._handle_capture,
                        State.ENROLLED: self._handle_enrolled,
                        State.VERIFYING: self._handle_capture,
                        State.RESULT: self._handle_result,
                    }[self._state]
                    handler(frame, landmarks)

                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if not self._process_key(key):
                        break

        except RuntimeError as exc:
            logger.error("Fatal: %s", exc)
            sys.exit(1)
        finally:
            cv2.destroyAllWindows()
            logger.info("Application exited.")

    # ── state handlers ──────────────────────────────────────────────

    def _handle_idle(self, frame: np.ndarray, landmarks: Optional[np.ndarray]) -> None:
        draw_idle_screen(frame, enrolled=self._store.is_enrolled)

    def _handle_enrolled(self, frame: np.ndarray, landmarks: Optional[np.ndarray]) -> None:
        draw_enrolled_screen(frame)

    def _handle_result(self, frame: np.ndarray, landmarks: Optional[np.ndarray]) -> None:
        draw_result_screen(frame, self._result_success)

    def _handle_capture(self, frame: np.ndarray, landmarks: Optional[np.ndarray]) -> None:
        """Shared handler for ENROLLING and VERIFYING states using timer-based single-frame capture."""
        mode_label = "Enroll" if self._state == State.ENROLLING else "Verify"

        # ── Pre-countdown pause between gestures ──
        if self._pre_countdown_active:
            elapsed_pre = time.time() - self._pre_countdown_start
            remaining = max(0.0, self._PRE_COUNTDOWN_SEC - elapsed_pre)
            draw_gesture_index(frame, self._current_gesture_idx + 1)
            draw_status(frame, f"Get ready...  {remaining:.1f}s", COLOR_YELLOW)
            if elapsed_pre >= self._PRE_COUNTDOWN_SEC:
                self._pre_countdown_active = False
                self._capture_start = time.time()
            return

        elapsed = time.time() - self._capture_start
        draw_progress_bar(frame, elapsed)
        draw_gesture_index(frame, self._current_gesture_idx + 1)

        # Show real-time finger state feedback
        if landmarks is not None:
            finger_states = detect_finger_states(landmarks)
            if finger_states is not None:
                gesture_class = classify_gesture(finger_states)
                draw_finger_states(frame, finger_states, gesture_class)
                draw_status(frame, f"{mode_label}: Hold gesture steady...", COLOR_BLUE)
            else:
                draw_hand_missing_warning(frame)
                draw_status(frame, f"{mode_label}: Hand detected but invalid!", COLOR_RED)
        else:
            draw_hand_missing_warning(frame)
            draw_status(frame, f"{mode_label}: Show your hand!", COLOR_RED)

        # When timer expires, capture the current gesture state
        if elapsed >= CAPTURE_DURATION_SEC:
            if landmarks is None:
                # No hand detected at timer expiration - restart timer
                draw_status(frame, "No hand detected! Retrying...", COLOR_RED)
                self._capture_start = time.time()
                return
            
            # Detect finger states at timer expiration
            finger_states = detect_finger_states(landmarks)
            if finger_states is None:
                # Invalid landmarks at timer expiration - restart timer
                draw_status(frame, "Invalid hand data! Retrying...", COLOR_RED)
                self._capture_start = time.time()
                return

            # Successfully captured gesture pattern
            self._gesture_buffer.append(finger_states)
            gesture_class = classify_gesture(finger_states)
            logger.info("Gesture %d/%d captured: %s (pattern: %s)",
                        self._current_gesture_idx + 1, NUM_GESTURES,
                        gesture_class, finger_states)
            self._current_gesture_idx += 1

            if self._current_gesture_idx >= NUM_GESTURES:
                self._finish_capture()
            else:
                # Start pre-countdown for next gesture
                self._pre_countdown_active = True
                self._pre_countdown_start = time.time()

    # ── capture lifecycle ───────────────────────────────────────────

    def _start_capture(self, state: State) -> None:
        """Begin an enrollment or verification capture session."""
        self._state = state
        self._gesture_buffer.clear()
        self._current_gesture_idx = 0
        self._pre_countdown_active = True
        self._pre_countdown_start = time.time()
        logger.info("Starting %s session.", state.value)

    def _finish_capture(self) -> None:
        """Called when all gestures have been captured."""
        if self._state == State.ENROLLING:
            self._store.enroll(self._gesture_buffer)
            logger.info("Enrollment complete.")
            self._state = State.ENROLLED
        elif self._state == State.VERIFYING:
            success = self._store.verify(self._gesture_buffer)
            self._result_success = success
            self._state = State.RESULT

    # ── key handling ────────────────────────────────────────────────

    def _process_key(self, key: int) -> bool:
        """
        Handle keyboard input. Returns False to quit.
        """
        if key == ord("q") or key == ord("Q"):
            return False

        if key == ord("e") or key == ord("E"):
            if self._state in (State.IDLE, State.ENROLLED, State.RESULT):
                self._store.reset()
                self._start_capture(State.ENROLLING)

        elif key == ord("v") or key == ord("V"):
            if self._state in (State.ENROLLED, State.RESULT):
                self._start_capture(State.VERIFYING)

        elif key == ord("r") or key == ord("R"):
            self._store.reset()
            self._state = State.IDLE
            logger.info("Reset to IDLE.")

        return True


def main() -> None:
    app = GestureLockApp()
    app.run()


if __name__ == "__main__":
    main()
