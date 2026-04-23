"""
Configuration file - all adjustable settings in one place.
"""

# Camera settings
CAMERA_INDEX: int = 0  # Which camera to use (0 = first camera)
CAMERA_WIDTH: int = 1280  # Resolution width in pixels
CAMERA_HEIGHT: int = 720  # Resolution height in pixels

# Gesture capture settings
CAPTURE_DURATION_SEC: float = 3.0  # How long to hold each gesture (seconds)
NUM_GESTURES: int = 3  # Number of gestures in a password sequence

# Finger extension detection thresholds
EXTENSION_THRESHOLD_X: float = 0.05  # Thumb extension threshold (horizontal distance)
EXTENSION_THRESHOLD_Y: float = 0.0  # Finger extension threshold (vertical distance)

# UI settings
WINDOW_NAME: str = "Gesture Lock"
FONT_SCALE: float = 0.8
FONT_THICKNESS: int = 2

# Colors in BGR format
COLOR_BLUE = (255, 180, 50)
COLOR_GREEN = (80, 220, 80)
COLOR_RED = (60, 60, 230)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_DARK_BG = (30, 30, 30)
COLOR_ACCENT = (255, 160, 0)
COLOR_YELLOW = (0, 230, 255)
