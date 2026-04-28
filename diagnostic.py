import sys
import os

print('=== PYTHON INFO ===')
print('Python:', sys.version)
print('Executable:', sys.executable)

print('\n=== MEDIAPIPE INFO ===')
import mediapipe as mp
print('MediaPipe version:', mp.__version__)
print('MediaPipe location:', mp.__file__)
print('Has mp.solutions:', hasattr(mp, 'solutions'))

print('\n=== IMPORT TESTS ===')
try:
    from mediapipe.python.solutions import hands
    print('✓ mediapipe.python.solutions.hands works')
except Exception as e:
    print('✗ mediapipe.python.solutions.hands:', e)

try:
    import mediapipe.solutions.hands
    print('✓ mediapipe.solutions.hands works')
except Exception as e:
    print('✗ mediapipe.solutions.hands:', e)

try:
    mp_hands = mp.solutions.hands
    print('✓ mp.solutions.hands works')
except Exception as e:
    print('✗ mp.solutions.hands:', e)

print('\n=== CAPTURE.PY CONTENT (lines 20-45) ===')
with open('src/capture.py', 'r') as f:
    lines = f.readlines()
    print(''.join(lines[19:45]))

print('\n=== GIT STATUS ===')
os.system('git log -1 --oneline')

print('\n=== TRYING TO IMPORT src.capture ===')
try:
    from src.capture import HandCapture
    print('✓ src.capture.HandCapture imported successfully')
except Exception as e:
    print('✗ Failed to import src.capture.HandCapture:')
    import traceback
    traceback.print_exc()
