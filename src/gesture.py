"""
Gesture detection module - detects which fingers are extended or curled.

Approach:
- Check each finger to see if it's extended (up) or curled (down)
- Return a 5-element boolean array: [thumb, index, middle, ring, pinky]
- Classify gestures by counting extended fingers (Fist=0, One=1, Two=2, etc.)
"""

from __future__ import annotations
import logging
from typing import Optional
import numpy as np

try:
    from src.config import EXTENSION_THRESHOLD_X
except ImportError:
    from config import EXTENSION_THRESHOLD_X

logger = logging.getLogger(__name__)

# MediaPipe hand landmarks: 21 points numbered 0-20
# 0=WRIST, 1-4=THUMB, 5-8=INDEX, 9-12=MIDDLE, 13-16=RING, 17-20=PINKY
THUMB_TIP = 4
THUMB_KNUCKLE = 2

FINGER_TIPS = [8, 12, 16, 20]  # Index, middle, ring, pinky tips
FINGER_KNUCKLES = [5, 9, 13, 17]  # Index, middle, ring, pinky knuckles

GESTURE_CLASSES = ["Fist", "One", "Two", "Three", "Four", "Five"]


def detect_finger_states(landmarks: np.ndarray) -> Optional[np.ndarray]:
    """
    Detect which fingers are extended or curled.
    
    Args:
        landmarks: (21, 3) array of hand landmark coordinates from MediaPipe
        
    Returns:
        (5,) boolean array [thumb, index, middle, ring, pinky] where True = extended
        Returns None if input is invalid
    """
    # Validate input
    if landmarks is None or landmarks.shape != (21, 3):
        logger.warning(f"Invalid landmark shape: expected (21, 3), got {landmarks.shape if landmarks is not None else None}")
        return None
    
    if not np.all(np.isfinite(landmarks)):
        logger.warning("Landmarks contain NaN or Inf values")
        return None
    
    finger_states = np.zeros(5, dtype=bool)
    
    # Detect thumb extension using horizontal distance (X-axis)
    # The thumb extends sideways (left/right) rather than up/down
    # Extended: thumb tip is significantly farther in X from wrist than thumb base
    # Retracted: thumb tip X is close to thumb base X
    wrist = landmarks[0]
    thumb_base = landmarks[2]  # Thumb MCP joint
    thumb_tip = landmarks[4]
    
    # Calculate horizontal distances from wrist
    base_x_dist = abs(thumb_base[0] - wrist[0])
    tip_x_dist = abs(thumb_tip[0] - wrist[0])
    
    # Threshold: tip must be at least 0.04 (4% of frame width) farther than base
    THUMB_EXTENSION_THRESHOLD = 0.04
    finger_states[0] = (tip_x_dist - base_x_dist) > THUMB_EXTENSION_THRESHOLD
    
    # Detect finger extensions by comparing tip and knuckle Y-coordinates
    # Extended if tip is significantly above knuckle (smaller Y value)
    Y_THRESHOLD = 0.03  # 3% of image height
    
    for i, (tip_idx, knuckle_idx) in enumerate(zip(FINGER_TIPS, FINGER_KNUCKLES)):
        tip_y = landmarks[tip_idx, 1]
        knuckle_y = landmarks[knuckle_idx, 1]
        finger_states[i + 1] = (knuckle_y - tip_y) > Y_THRESHOLD
    
    return finger_states


def classify_gesture(finger_states: np.ndarray) -> str:
    """
    Classify gesture by counting extended fingers.
    
    Args:
        finger_states: (5,) boolean array of finger extension states
        
    Returns:
        Gesture name: "Fist", "One", "Two", "Three", "Four", or "Five"
    """
    count = int(np.sum(finger_states))
    count = max(0, min(5, count))  # Clamp to [0, 5]
    return GESTURE_CLASSES[count]


def compare_patterns(pattern1: np.ndarray, pattern2: np.ndarray) -> bool:
    """
    Compare two gesture patterns for exact equality.
    
    Args:
        pattern1, pattern2: (5,) boolean arrays
        
    Returns:
        True if patterns match exactly, False otherwise
    """
    if pattern1.shape != (5,) or pattern2.shape != (5,):
        logger.warning(f"Invalid pattern shapes: {pattern1.shape}, {pattern2.shape}")
        return False
    
    return bool(np.array_equal(pattern1, pattern2))
