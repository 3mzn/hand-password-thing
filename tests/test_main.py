"""
Unit tests for predefined gesture detection based on binary finger states.
"""

import numpy as np
import pytest

from src.gesture import classify_gesture, compare_patterns, detect_finger_states
from src.password_store import PasswordStore


# ── Test Landmark Helpers ──────────────────────────────────────────

def _make_fist() -> np.ndarray:
    """
    Simulated fist: all fingertips curled down (below knuckles).
    Expected pattern: [False, False, False, False, False] = "Fist"
    """
    lm = np.zeros((21, 3))
    lm[0] = [0.5, 0.5, 0]  # wrist
    
    # Thumb: retracted (tip X is close to base X, not extended sideways)
    lm[1] = [0.45, 0.45, 0]  # CMC
    lm[2] = [0.48, 0.42, 0]  # MCP (base) - X distance from wrist: abs(0.48-0.5) = 0.02
    lm[3] = [0.49, 0.44, 0]  # IP (middle)
    lm[4] = [0.50, 0.46, 0]  # TIP - X distance from wrist: abs(0.50-0.5) = 0.00 (not extended)
    
    # Index: tip below knuckle (curled)
    lm[5] = [0.5, 0.3, 0]  # index knuckle
    lm[8] = [0.5, 0.32, 0]  # index tip
    
    # Middle: tip below knuckle (curled)
    lm[9] = [0.6, 0.4, 0]  # middle knuckle
    lm[12] = [0.6, 0.42, 0]  # middle tip
    
    # Ring: tip below knuckle (curled)
    lm[13] = [0.7, 0.4, 0]  # ring knuckle
    lm[16] = [0.7, 0.42, 0]  # ring tip
    
    # Pinky: tip below knuckle (curled)
    lm[17] = [0.8, 0.4, 0]  # pinky knuckle
    lm[20] = [0.8, 0.42, 0]  # pinky tip
    
    return lm


def _make_open_palm() -> np.ndarray:
    """
    Simulated open palm: all fingers extended upward.
    Expected pattern: [True, True, True, True, True] = "Five"
    """
    lm = np.zeros((21, 3))
    lm[0] = [0.5, 0.5, 0]  # wrist
    
    # Thumb: extended (tip X is far from wrist, extended sideways)
    lm[1] = [0.45, 0.45, 0]  # CMC
    lm[2] = [0.42, 0.42, 0]  # MCP (base) - X distance from wrist: abs(0.42-0.5) = 0.08
    lm[3] = [0.35, 0.35, 0]  # IP (middle)
    lm[4] = [0.25, 0.25, 0]  # TIP - X distance from wrist: abs(0.25-0.5) = 0.25 (extended!)
    
    # Index: tip above knuckle (extended)
    lm[5] = [0.5, 0.4, 0]  # index knuckle
    lm[8] = [0.5, 0.05, 0]  # index tip (well above knuckle)
    
    # Middle: tip above knuckle (extended)
    lm[9] = [0.6, 0.4, 0]  # middle knuckle
    lm[12] = [0.6, 0.05, 0]  # middle tip
    
    # Ring: tip above knuckle (extended)
    lm[13] = [0.7, 0.4, 0]  # ring knuckle
    lm[16] = [0.7, 0.05, 0]  # ring tip
    
    # Pinky: tip above knuckle (extended)
    lm[17] = [0.8, 0.4, 0]  # pinky knuckle
    lm[20] = [0.8, 0.05, 0]  # pinky tip
    
    return lm


def _make_peace_sign() -> np.ndarray:
    """
    Simulated peace sign: index and middle fingers extended.
    Expected pattern: [False, True, True, False, False] = "Two"
    """
    lm = np.zeros((21, 3))
    lm[0] = [0.5, 0.5, 0]  # wrist
    
    # Thumb: retracted (tip X close to base X)
    lm[1] = [0.45, 0.45, 0]  # CMC
    lm[2] = [0.48, 0.42, 0]  # MCP (base)
    lm[3] = [0.49, 0.44, 0]  # IP
    lm[4] = [0.50, 0.46, 0]  # TIP - not extended sideways
    
    # Index: extended
    lm[5] = [0.5, 0.4, 0]
    lm[8] = [0.5, 0.05, 0]  # well above knuckle
    
    # Middle: extended
    lm[9] = [0.6, 0.4, 0]
    lm[12] = [0.6, 0.05, 0]  # well above knuckle
    
    # Ring: curled
    lm[13] = [0.7, 0.4, 0]
    lm[16] = [0.7, 0.42, 0]
    
    # Pinky: curled
    lm[17] = [0.8, 0.4, 0]
    lm[20] = [0.8, 0.42, 0]
    
    return lm


def _make_thumbs_up() -> np.ndarray:
    """
    Simulated thumbs up: only thumb extended.
    Expected pattern: [True, False, False, False, False] = "One"
    """
    lm = np.zeros((21, 3))
    lm[0] = [0.5, 0.5, 0]  # wrist
    
    # Thumb: extended (tip X is far from wrist)
    lm[1] = [0.45, 0.45, 0]  # CMC
    lm[2] = [0.42, 0.42, 0]  # MCP (base) - X distance: abs(0.42-0.5) = 0.08
    lm[3] = [0.35, 0.35, 0]  # IP (middle)
    lm[4] = [0.25, 0.25, 0]  # TIP - X distance: abs(0.25-0.5) = 0.25 (extended!)
    
    # Index: curled
    lm[5] = [0.5, 0.4, 0]
    lm[8] = [0.5, 0.42, 0]  # tip only slightly below knuckle
    
    # Middle: curled
    lm[9] = [0.6, 0.4, 0]
    lm[12] = [0.6, 0.42, 0]
    
    # Ring: curled
    lm[13] = [0.7, 0.4, 0]
    lm[16] = [0.7, 0.42, 0]
    
    # Pinky: curled
    lm[17] = [0.8, 0.4, 0]
    lm[20] = [0.8, 0.42, 0]
    
    return lm


# ── Finger State Detection Tests ───────────────────────────────────

class TestDetectFingerStates:
    def test_fist_gesture(self) -> None:
        """Test that a fist is detected as all fingers curled."""
        lm = _make_fist()
        states = detect_finger_states(lm)
        assert states is not None
        assert states.shape == (5,)
        assert states.dtype == bool
        # All fingers should be curled (False)
        assert not states[0]  # thumb
        assert not states[1]  # index
        assert not states[2]  # middle
        assert not states[3]  # ring
        assert not states[4]  # pinky
    
    def test_open_palm_gesture(self) -> None:
        """Test that an open palm is detected as all fingers extended."""
        lm = _make_open_palm()
        states = detect_finger_states(lm)
        assert states is not None
        assert states.shape == (5,)
        # All fingers should be extended (True)
        assert states[0]  # thumb
        assert states[1]  # index
        assert states[2]  # middle
        assert states[3]  # ring
        assert states[4]  # pinky
    
    def test_peace_sign_gesture(self) -> None:
        """Test that a peace sign is detected as index and middle extended."""
        lm = _make_peace_sign()
        states = detect_finger_states(lm)
        assert states is not None
        assert not states[0]  # thumb curled
        assert states[1]      # index extended
        assert states[2]      # middle extended
        assert not states[3]  # ring curled
        assert not states[4]  # pinky curled
    
    def test_thumbs_up_gesture(self) -> None:
        """Test that a thumbs up is detected as only thumb extended."""
        lm = _make_thumbs_up()
        states = detect_finger_states(lm)
        assert states is not None
        assert states[0]      # thumb extended
        assert not states[1]  # index curled
        assert not states[2]  # middle curled
        assert not states[3]  # ring curled
        assert not states[4]  # pinky curled
    
    def test_invalid_shape_returns_none(self) -> None:
        """Test that invalid landmark shape returns None."""
        invalid_lm = np.zeros((10, 2))
        states = detect_finger_states(invalid_lm)
        assert states is None
    
    def test_none_input_returns_none(self) -> None:
        """Test that None input returns None."""
        states = detect_finger_states(None)
        assert states is None
    
    def test_nan_values_return_none(self) -> None:
        """Test that landmarks with NaN values return None."""
        lm = _make_fist()
        lm[5, 1] = np.nan  # inject NaN
        states = detect_finger_states(lm)
        assert states is None
    
    def test_inf_values_return_none(self) -> None:
        """Test that landmarks with Inf values return None."""
        lm = _make_fist()
        lm[8, 0] = np.inf  # inject Inf
        states = detect_finger_states(lm)
        assert states is None


# ── Gesture Classification Tests ───────────────────────────────────

class TestClassifyGesture:
    def test_fist_classification(self) -> None:
        """Test that zero extended fingers is classified as 'Fist'."""
        pattern = np.array([False, False, False, False, False], dtype=bool)
        assert classify_gesture(pattern) == "Fist"
    
    def test_one_finger_classification(self) -> None:
        """Test that one extended finger is classified as 'One'."""
        # Test various single-finger combinations
        patterns = [
            np.array([True, False, False, False, False], dtype=bool),  # thumb
            np.array([False, True, False, False, False], dtype=bool),  # index
            np.array([False, False, True, False, False], dtype=bool),  # middle
            np.array([False, False, False, True, False], dtype=bool),  # ring
            np.array([False, False, False, False, True], dtype=bool),  # pinky
        ]
        for pattern in patterns:
            assert classify_gesture(pattern) == "One"
    
    def test_two_fingers_classification(self) -> None:
        """Test that two extended fingers is classified as 'Two'."""
        # Test various two-finger combinations
        patterns = [
            np.array([False, True, True, False, False], dtype=bool),  # index + middle
            np.array([True, False, False, False, True], dtype=bool),  # thumb + pinky
            np.array([False, False, True, True, False], dtype=bool),  # middle + ring
        ]
        for pattern in patterns:
            assert classify_gesture(pattern) == "Two"
    
    def test_three_fingers_classification(self) -> None:
        """Test that three extended fingers is classified as 'Three'."""
        pattern = np.array([False, True, True, True, False], dtype=bool)
        assert classify_gesture(pattern) == "Three"
    
    def test_four_fingers_classification(self) -> None:
        """Test that four extended fingers is classified as 'Four'."""
        pattern = np.array([False, True, True, True, True], dtype=bool)
        assert classify_gesture(pattern) == "Four"
    
    def test_five_fingers_classification(self) -> None:
        """Test that five extended fingers is classified as 'Five'."""
        pattern = np.array([True, True, True, True, True], dtype=bool)
        assert classify_gesture(pattern) == "Five"


# ── Pattern Comparison Tests ────────────────────────────────────────

class TestComparePatterns:
    def test_identical_patterns_match(self) -> None:
        """Test that identical patterns return True."""
        pattern = np.array([True, False, True, False, True], dtype=bool)
        assert compare_patterns(pattern, pattern) is True
    
    def test_different_patterns_dont_match(self) -> None:
        """Test that different patterns return False."""
        pattern1 = np.array([True, False, True, False, True], dtype=bool)
        pattern2 = np.array([False, True, False, True, False], dtype=bool)
        assert compare_patterns(pattern1, pattern2) is False
    
    def test_single_bit_difference(self) -> None:
        """Test that patterns differing in one position don't match."""
        pattern1 = np.array([True, True, True, True, True], dtype=bool)
        pattern2 = np.array([True, True, False, True, True], dtype=bool)
        assert compare_patterns(pattern1, pattern2) is False
    
    def test_all_false_patterns_match(self) -> None:
        """Test that two all-False patterns match."""
        pattern1 = np.array([False, False, False, False, False], dtype=bool)
        pattern2 = np.array([False, False, False, False, False], dtype=bool)
        assert compare_patterns(pattern1, pattern2) is True
    
    def test_all_true_patterns_match(self) -> None:
        """Test that two all-True patterns match."""
        pattern1 = np.array([True, True, True, True, True], dtype=bool)
        pattern2 = np.array([True, True, True, True, True], dtype=bool)
        assert compare_patterns(pattern1, pattern2) is True


# ── PasswordStore Tests ─────────────────────────────────────────────

class TestPasswordStore:
    def test_enroll_and_verify_success(self) -> None:
        """Test successful enrollment and verification with matching patterns."""
        store = PasswordStore()
        
        # Create gesture sequence
        gestures = [
            np.array([False, False, False, False, False], dtype=bool),  # Fist
            np.array([False, True, True, False, False], dtype=bool),    # Peace
            np.array([True, True, True, True, True], dtype=bool),       # Open palm
        ]
        
        # Enroll
        store.enroll(gestures)
        assert store.is_enrolled
        
        # Verify with same gestures
        success = store.verify(gestures)
        assert success is True
    
    def test_verify_failure_with_different_patterns(self) -> None:
        """Test verification failure with non-matching patterns."""
        store = PasswordStore()
        
        # Enroll with one sequence
        enrolled_gestures = [
            np.array([False, False, False, False, False], dtype=bool),
            np.array([False, True, True, False, False], dtype=bool),
            np.array([True, True, True, True, True], dtype=bool),
        ]
        store.enroll(enrolled_gestures)
        
        # Verify with different sequence
        different_gestures = [
            np.array([True, True, True, True, True], dtype=bool),
            np.array([False, False, False, False, False], dtype=bool),
            np.array([False, True, False, False, False], dtype=bool),
        ]
        success = store.verify(different_gestures)
        assert success is False
    
    def test_verify_before_enroll_raises(self) -> None:
        """Test that verifying before enrollment raises an error."""
        store = PasswordStore()
        gestures = [
            np.array([False, False, False, False, False], dtype=bool),
            np.array([False, True, True, False, False], dtype=bool),
            np.array([True, True, True, True, True], dtype=bool),
        ]
        with pytest.raises(RuntimeError, match="No password enrolled"):
            store.verify(gestures)
    
    def test_enroll_wrong_length_raises(self) -> None:
        """Test that enrolling wrong number of gestures raises an error."""
        store = PasswordStore()
        gestures = [
            np.array([False, False, False, False, False], dtype=bool),
        ]
        with pytest.raises(ValueError, match="Expected 3 gestures"):
            store.enroll(gestures)
    
    def test_reset_clears_data(self) -> None:
        """Test that reset clears enrolled data."""
        store = PasswordStore()
        gestures = [
            np.array([False, False, False, False, False], dtype=bool),
            np.array([False, True, True, False, False], dtype=bool),
            np.array([True, True, True, True, True], dtype=bool),
        ]
        store.enroll(gestures)
        assert store.is_enrolled
        
        store.reset()
        assert not store.is_enrolled
