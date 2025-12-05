import pyautogui

# --- CONFIGURATION ---
# gotta go fast, no built-in delays
pyautogui.PAUSE = 0

# steering feel
DEADZONE_ANGLE = 2.0      # ignore tiny jitters
MAX_TURN_ANGLE = 50.0     # how much rotation = full lock
SMOOTHING_ALPHA = 0.2     # smooth out the shakes

# pwm stuff to fake analog input on a keyboard
# 0.1s seems to be the sweet spot so the game actually registers the key press
PWM_CYCLE_SECONDS = 0.1

# key bindings
KEY_UP = 'w'
KEY_DOWN = 's'
KEY_LEFT = 'a'
KEY_RIGHT = 'd'

# speed hacks
# we don't need to run the heavy AI every single frame.
# skipping every other frame doubles our FPS without hurting control much.
PROCESS_EVERY_N_FRAMES = 2 
