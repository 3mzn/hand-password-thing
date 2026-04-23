"""
Webcam + MediaPipe Hands wrapper.
Handles camera lifecycle and hand landmark extraction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

try:
    from src.config import CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH
except ImportError:
    from config import CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    try:
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
    except AttributeError:
        # Fallback for newer or fragmented Mediapipe installations
        from mediapipe.python.solutions import hands as mp_hands
        from mediapipe.python.solutions import drawing_utils as mp_drawing
        from mediapipe.python.solutions import drawing_styles as mp_drawing_styles
except (ImportError, AttributeError) as e:
    logger.error("Failed to import MediaPipe solutions: %s", e)
    # Final fallback attempt
    try:
        import mediapipe.solutions.hands as mp_hands
        import mediapipe.solutions.drawing_utils as mp_drawing
        import mediapipe.solutions.drawing_styles as mp_drawing_styles
    except ImportError:
        raise ImportError(
            "Could not find MediaPipe solutions. Please ensure mediapipe is installed correctly."
        ) from e


@dataclass
class FrameResult:
    """Container for a single processed frame."""
    frame: np.ndarray                         # BGR image
    landmarks: Optional[np.ndarray] = None    # (21, 3) if hand detected


class HandCapture:
    """Manages the webcam and MediaPipe hand detector."""

    def __init__(self, camera_index: int = CAMERA_INDEX) -> None:
        self._cap: Optional[cv2.VideoCapture] = None
        self._hands: Optional[mp_hands.Hands] = None
        self._camera_index = camera_index

    # ── lifecycle ───────────────────────────────────────────────────

    def open(self) -> None:
        """Open the camera and initialise MediaPipe."""
        logger.info("Opening camera %d", self._camera_index)
        self._cap = cv2.VideoCapture(self._camera_index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Cannot open camera index {self._camera_index}. "
                "Check that a webcam is connected."
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        logger.info("Camera and MediaPipe initialised.")

    def close(self) -> None:
        """Release all resources."""
        if self._hands is not None:
            self._hands.close()
            self._hands = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("Camera released.")

    # ── frame processing ────────────────────────────────────────────

    def get_frame(self) -> FrameResult:
        """
        Read one frame, run hand detection, and return the result.
        Draws the hand skeleton directly onto the returned frame.
        """
        if self._cap is None or not self._cap.isOpened():
            raise RuntimeError("Camera is not open. Call open() first.")

        success, frame = self._cap.read()
        if not success:
            raise RuntimeError("Failed to read frame from camera.")

        # Flip horizontally so it feels like a mirror
        frame = cv2.flip(frame, 1)

        # Convert BGR → RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)  # type: ignore[union-attr]

        landmarks = None
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]

            # Draw skeleton
            mp_drawing.draw_landmarks(
                frame,
                hand,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style(),
            )

            # Extract (21, 3) array
            landmarks = np.array(
                [[lm.x, lm.y, lm.z] for lm in hand.landmark],
                dtype=np.float64,
            )

        return FrameResult(frame=frame, landmarks=landmarks)

    # ── context manager ─────────────────────────────────────────────

    def __enter__(self) -> "HandCapture":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
