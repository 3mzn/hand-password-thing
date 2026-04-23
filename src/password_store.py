"""
Password store - manages gesture passwords.

Stores enrolled gesture patterns in memory (not saved to disk).
"""

from __future__ import annotations
import logging
from typing import List, Optional
import numpy as np

try:
    from src.config import NUM_GESTURES
    from src.gesture import compare_patterns
except ImportError:
    from config import NUM_GESTURES
    from gesture import compare_patterns

logger = logging.getLogger(__name__)


class PasswordStore:
    """Manages gesture password enrollment and verification."""

    def __init__(self) -> None:
        self._enrolled: Optional[List[np.ndarray]] = None  # Stored gesture patterns

    @property
    def is_enrolled(self) -> bool:
        """Check if a password has been enrolled."""
        return self._enrolled is not None

    def enroll(self, gestures: List[np.ndarray]) -> None:
        """
        Enroll a new gesture password.
        
        Args:
            gestures: List of NUM_GESTURES (5,) boolean arrays
        """
        if len(gestures) != NUM_GESTURES:
            raise ValueError(f"Expected {NUM_GESTURES} gestures, got {len(gestures)}")
        
        # Validate each gesture is a (5,) boolean array
        for i, g in enumerate(gestures):
            if g.shape != (5,) or g.dtype != bool:
                raise ValueError(
                    f"Gesture {i} has invalid shape/type: {g.shape}, {g.dtype}. "
                    f"Expected (5,) boolean array"
                )
        
        self._enrolled = [g.copy() for g in gestures]
        logger.info("Enrolled %d gestures.", len(gestures))

    def verify(self, candidates: List[np.ndarray]) -> bool:
        """
        Verify candidate gestures against enrolled password.
        
        Args:
            candidates: List of NUM_GESTURES (5,) boolean arrays
            
        Returns:
            True if all gestures match, False otherwise
        """
        if self._enrolled is None:
            raise RuntimeError("No password enrolled yet.")
        if len(candidates) != NUM_GESTURES:
            raise ValueError(f"Expected {NUM_GESTURES} gestures, got {len(candidates)}")

        # Compare each gesture pattern for exact match
        all_match = True
        for i, (enrolled_pattern, candidate_pattern) in enumerate(zip(self._enrolled, candidates)):
            if not compare_patterns(enrolled_pattern, candidate_pattern):
                all_match = False
                logger.info("Gesture %d/%d FAILED (patterns don't match)", i + 1, len(self._enrolled))
        
        if all_match:
            logger.info("Verification PASSED.")
        else:
            logger.info("Verification FAILED.")
        
        return all_match

    def reset(self) -> None:
        """Clear all stored data."""
        self._enrolled = None
        logger.info("Password store reset.")
