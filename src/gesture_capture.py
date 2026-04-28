"""
Gesture capture module for enrolling and verifying gesture passwords.

This module provides a reusable interface for capturing gesture passwords
through the camera using MediaPipe hand detection. It supports two modes:
- "enroll": Capture a new gesture password sequence
- "verify": Capture gestures for verification against an existing password
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import cv2
import numpy as np

from src.capture import HandCapture
from src.config import (
    CAPTURE_DURATION_SEC,
    COLOR_BLUE,
    COLOR_RED,
    COLOR_YELLOW,
    NUM_GESTURES,
    WINDOW_NAME,
)
from src.gesture import classify_gesture, detect_finger_states
from src.ui import (
    draw_finger_states,
    draw_gesture_index,
    draw_hand_missing_warning,
    draw_progress_bar,
    draw_status,
)

logger = logging.getLogger(__name__)


class GestureCapture:
    """Handles gesture password capture for enrollment and verification."""

    def __init__(self) -> None:
        self._capture = HandCapture()
        self._gesture_buffer: list[np.ndarray] = []
        self._capture_start: float = 0.0
        self._current_gesture_idx: int = 0
        self._pre_countdown_start: float = 0.0
        self._pre_countdown_active: bool = False
        self._PRE_COUNTDOWN_SEC: float = 1.5

    def capture_gesture_password(self, mode: str) -> Optional[list[int]]:
        """
        Capture a gesture password sequence.

        Args:
            mode: Either "enroll" or "verify" to control instructions displayed

        Returns:
            List of gesture class indices (0-5 for Fist, One, Two, Three, Four, Five)
            Returns None if capture was cancelled (user pressed Q)
        """
        if mode not in ("enroll", "verify"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'enroll' or 'verify'")

        self._gesture_buffer.clear()
        self._current_gesture_idx = 0
        self._pre_countdown_active = True
        self._pre_countdown_start = time.time()

        logger.info("Starting gesture capture in %s mode", mode)

        try:
            with self._capture:
                self._display_instructions(mode)
                
                while self._current_gesture_idx < NUM_GESTURES:
                    frame_result = self._capture.get_frame()
                    frame = frame_result.frame
                    landmarks = frame_result.landmarks

                    self._handle_capture_frame(frame, landmarks, mode)

                    cv2.imshow(WINDOW_NAME, frame)
                    key = cv2.waitKey(1) & 0xFF
                    
                    if key == ord("q") or key == ord("Q"):
                        logger.info("Gesture capture cancelled by user")
                        cv2.destroyWindow(WINDOW_NAME)
                        return None

                # Convert gesture patterns to class indices
                gesture_indices = []
                for pattern in self._gesture_buffer:
                    gesture_class = classify_gesture(pattern)
                    # Map gesture class name to index (Fist=0, One=1, ..., Five=5)
                    class_index = ["Fist", "One", "Two", "Three", "Four", "Five"].index(gesture_class)
                    gesture_indices.append(class_index)

                logger.info("Gesture capture complete: %s", gesture_indices)
                cv2.destroyWindow(WINDOW_NAME)
                return gesture_indices

        except RuntimeError as exc:
            logger.error("Gesture capture failed: %s", exc)
            cv2.destroyWindow(WINDOW_NAME)
            return None

    def _display_instructions(self, mode: str) -> None:
        """
        Display mode-specific instructions to the user.

        Args:
            mode: Either "enroll" or "verify"
        """
        if mode == "enroll":
            logger.info("ENROLL MODE: Set up a new gesture password")
            logger.info("You will perform %d gestures, each held for %.1f seconds", 
                       NUM_GESTURES, CAPTURE_DURATION_SEC)
        elif mode == "verify":
            logger.info("VERIFY MODE: Enter your gesture password")
            logger.info("Perform your %d-gesture password sequence", NUM_GESTURES)

    def _handle_capture_frame(
        self, 
        frame: np.ndarray, 
        landmarks: Optional[np.ndarray],
        mode: str
    ) -> None:
        """
        Process a single frame during gesture capture.

        Args:
            frame: The camera frame to draw on
            landmarks: Hand landmarks from MediaPipe (or None if no hand detected)
            mode: Either "enroll" or "verify"
        """
        mode_label = "Enroll" if mode == "enroll" else "Verify"

        # Pre-countdown pause between gestures
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
            logger.info(
                "Gesture %d/%d captured: %s (pattern: %s)",
                self._current_gesture_idx + 1,
                NUM_GESTURES,
                gesture_class,
                finger_states,
            )
            self._current_gesture_idx += 1

            if self._current_gesture_idx < NUM_GESTURES:
                # Start pre-countdown for next gesture
                self._pre_countdown_active = True
                self._pre_countdown_start = time.time()
