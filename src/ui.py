"""
OpenCV overlay rendering for the Gesture Lock UI.

Draws countdown timers, status text, progress bars, instructions,
and result screens directly onto the camera frame.
"""

from __future__ import annotations

import cv2
import numpy as np

try:
    from src.config import (
        CAPTURE_DURATION_SEC,
        COLOR_ACCENT,
        COLOR_BLACK,
        COLOR_BLUE,
        COLOR_DARK_BG,
        COLOR_GREEN,
        COLOR_RED,
        COLOR_WHITE,
        COLOR_YELLOW,
        FONT_SCALE,
        FONT_THICKNESS,
        NUM_GESTURES,
    )
except ImportError:
    from config import (
        CAPTURE_DURATION_SEC,
        COLOR_ACCENT,
        COLOR_BLACK,
        COLOR_BLUE,
        COLOR_DARK_BG,
        COLOR_GREEN,
        COLOR_RED,
        COLOR_WHITE,
        COLOR_YELLOW,
        FONT_SCALE,
        FONT_THICKNESS,
        NUM_GESTURES,
    )

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SMALL = cv2.FONT_HERSHEY_SIMPLEX


def _put_text_centered(
    frame: np.ndarray,
    text: str,
    y: int,
    color: tuple,
    scale: float = FONT_SCALE,
    thickness: int = FONT_THICKNESS,
) -> None:
    """Draw centred text at vertical position *y*."""
    (tw, th), _ = cv2.getTextSize(text, FONT, scale, thickness)
    x = (frame.shape[1] - tw) // 2
    # Shadow for readability
    cv2.putText(frame, text, (x + 2, y + 2), FONT, scale, COLOR_BLACK, thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), FONT, scale, color, thickness, cv2.LINE_AA)


def _draw_rounded_rect(
    frame: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    color: tuple,
    radius: int = 12,
    fill: bool = True,
) -> None:
    """Draw a filled rounded rectangle."""
    overlay = frame.copy()
    if fill:
        cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        cv2.circle(overlay, (x1 + radius, y1 + radius), radius, color, -1)
        cv2.circle(overlay, (x2 - radius, y1 + radius), radius, color, -1)
        cv2.circle(overlay, (x1 + radius, y2 - radius), radius, color, -1)
        cv2.circle(overlay, (x2 - radius, y2 - radius), radius, color, -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)


def draw_progress_bar(
    frame: np.ndarray,
    elapsed: float,
    duration: float = CAPTURE_DURATION_SEC,
) -> None:
    """Draw a horizontal progress / countdown bar at the top."""
    h, w = frame.shape[:2]
    bar_h = 16
    margin = 40
    progress = min(elapsed / duration, 1.0)

    # Background bar
    _draw_rounded_rect(frame, margin, 20, w - margin, 20 + bar_h, COLOR_DARK_BG)

    # Foreground
    fill_w = int((w - 2 * margin) * progress)
    if fill_w > 4:
        color = COLOR_GREEN if progress < 0.8 else COLOR_YELLOW
        _draw_rounded_rect(frame, margin, 20, margin + fill_w, 20 + bar_h, color)

    # Time remaining
    remaining = max(0.0, duration - elapsed)
    _put_text_centered(frame, f"{remaining:.1f}s", 58, COLOR_WHITE, 0.6, 1)


def draw_status(
    frame: np.ndarray,
    text: str,
    color: tuple = COLOR_WHITE,
) -> None:
    """Draw a status message near the bottom of the frame."""
    h = frame.shape[0]
    # Background panel
    _draw_rounded_rect(frame, 30, h - 80, frame.shape[1] - 30, h - 20, COLOR_DARK_BG)
    _put_text_centered(frame, text, h - 40, color, 0.75, 2)


def draw_gesture_index(
    frame: np.ndarray,
    current: int,
    total: int = NUM_GESTURES,
) -> None:
    """Draw gesture step indicator (e.g. 'Gesture 2 / 3')."""
    _put_text_centered(frame, f"Gesture  {current} / {total}", 100, COLOR_ACCENT, 0.9, 2)


def draw_finger_states(
    frame: np.ndarray,
    finger_states: np.ndarray | None,
    gesture_class: str | None,
) -> None:
    """
    Display real-time finger extension states and gesture class.
    
    Args:
        frame: BGR image to draw on
        finger_states: (5,) boolean array [thumb, index, middle, ring, pinky] or None
        gesture_class: Gesture class name ("Fist", "One", "Two", etc.) or None
        
    Visual Layout:
        Top-right corner shows:
        - Finger names with checkmarks (✓) for extended, crosses (✗) for curled
        - Current gesture class name
    """
    h, w = frame.shape[:2]
    
    # Panel dimensions
    panel_w = 200
    panel_h = 180
    panel_x = w - panel_w - 20
    panel_y = 20
    
    # Draw background panel
    _draw_rounded_rect(frame, panel_x, panel_y, panel_x + panel_w, panel_y + panel_h, COLOR_DARK_BG)
    
    if finger_states is None:
        # Show "Hand not detected" message
        text_y = panel_y + 90
        cv2.putText(frame, "Hand not", (panel_x + 40, text_y), FONT_SMALL, 0.6, COLOR_RED, 1, cv2.LINE_AA)
        cv2.putText(frame, "detected", (panel_x + 40, text_y + 25), FONT_SMALL, 0.6, COLOR_RED, 1, cv2.LINE_AA)
        return
    
    # Finger names
    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    
    # Draw finger states
    y_offset = panel_y + 30
    for i, (name, extended) in enumerate(zip(finger_names, finger_states)):
        y = y_offset + i * 25
        
        # Draw finger name
        cv2.putText(frame, f"{name}:", (panel_x + 15, y), FONT_SMALL, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)
        
        # Draw checkmark or cross
        symbol = "✓" if extended else "✗"
        symbol_color = COLOR_GREEN if extended else COLOR_RED
        cv2.putText(frame, symbol, (panel_x + 140, y), FONT_SMALL, 0.7, symbol_color, 2, cv2.LINE_AA)
    
    # Draw gesture class name
    if gesture_class:
        class_y = panel_y + panel_h - 30
        cv2.putText(frame, "Class:", (panel_x + 15, class_y), FONT_SMALL, 0.5, COLOR_ACCENT, 1, cv2.LINE_AA)
        cv2.putText(frame, gesture_class, (panel_x + 15, class_y + 20), FONT_SMALL, 0.65, COLOR_YELLOW, 2, cv2.LINE_AA)


def draw_hand_missing_warning(frame: np.ndarray) -> None:
    """Draw a warning when no hand is detected."""
    h = frame.shape[0]
    _put_text_centered(frame, "No hand detected — show your hand", h // 2, COLOR_RED, 0.8, 2)


def draw_idle_screen(frame: np.ndarray, enrolled: bool) -> None:
    """Draw the idle / home screen instructions."""
    h, w = frame.shape[:2]
    # Semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), COLOR_BLACK, -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    _put_text_centered(frame, "GESTURE LOCK", h // 2 - 120, COLOR_ACCENT, 1.6, 3)
    _put_text_centered(frame, "Hand Gesture Password System", h // 2 - 70, COLOR_WHITE, 0.65, 1)

    y_start = h // 2 - 10
    if enrolled:
        _put_text_centered(frame, "[V]  Verify password", y_start, COLOR_GREEN, 0.7, 2)
        _put_text_centered(frame, "[E]  Re-enroll new password", y_start + 45, COLOR_BLUE, 0.7, 2)
    else:
        _put_text_centered(frame, "[E]  Enroll a new password", y_start, COLOR_BLUE, 0.7, 2)

    _put_text_centered(frame, "[R]  Reset   |   [Q]  Quit", y_start + 90, (150, 150, 150), 0.55, 1)


def draw_result_screen(frame: np.ndarray, success: bool) -> None:
    """Draw the verification result screen."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), COLOR_BLACK, -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    if success:
        _put_text_centered(frame, "ACCESS GRANTED", h // 2 - 40, COLOR_GREEN, 1.4, 3)
        _put_text_centered(frame, "Password verified successfully!", h // 2 + 20, COLOR_WHITE, 0.75, 2)
    else:
        _put_text_centered(frame, "ACCESS DENIED", h // 2 - 40, COLOR_RED, 1.4, 3)
        _put_text_centered(frame, "Gestures did not match.", h // 2 + 20, COLOR_WHITE, 0.75, 2)

    _put_text_centered(frame, "[R] Reset   |   [V] Retry   |   [Q] Quit", h // 2 + 110, (150, 150, 150), 0.55, 1)


def draw_enrolled_screen(frame: np.ndarray) -> None:
    """Draw confirmation after successful enrollment."""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), COLOR_BLACK, -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    _put_text_centered(frame, "PASSWORD SET", h // 2 - 60, COLOR_GREEN, 1.4, 3)
    _put_text_centered(frame, "3 gestures enrolled successfully!", h // 2, COLOR_WHITE, 0.7, 2)
    _put_text_centered(frame, "[V]  Verify now   |   [R]  Reset   |   [Q]  Quit",
                       h // 2 + 60, (150, 150, 150), 0.55, 1)
