import pyautogui
import time
import math
import config

class SteeringController:
    def __init__(self):
        self.last_cycle_start = time.time()
        self.is_key_physically_down = False
        self.current_pedal_state = None

    def update_steering(self, current_angle):
        """Calculates steering intensity and handles PWM key presses."""
        abs_angle = abs(current_angle)
        turn_direction = 'right' if current_angle > 0 else 'left'
        target_key = config.KEY_RIGHT if turn_direction == 'right' else config.KEY_LEFT
        opposite_key = config.KEY_LEFT if turn_direction == 'right' else config.KEY_RIGHT

        # Always release the opposite key
        pyautogui.keyUp(opposite_key)

        steering_intensity = 0.0
        status_text = "STRAIGHT"
        bar_color = (0, 255, 0)

        if abs_angle < config.DEADZONE_ANGLE:
            steering_intensity = 0.0
        else:
            # Calculate linear intensity (0.0 to 1.0)
            raw_intensity = (abs_angle - config.DEADZONE_ANGLE) / (config.MAX_TURN_ANGLE - config.DEADZONE_ANGLE)
            raw_intensity = min(max(raw_intensity, 0.0), 1.0)
            
            # magic sensitivity curve
            steering_intensity = math.pow(raw_intensity, 0.5)
            
            status_text = f"{turn_direction.upper()} {int(steering_intensity * 100)}%"
            bar_color = (0, int(255 * (1-steering_intensity)), int(255 * steering_intensity))

        # PWM Logic
        self._handle_pwm(steering_intensity, target_key)

        return steering_intensity, status_text, bar_color

    def _handle_pwm(self, intensity, target_key):
        if intensity == 0:
            if self.is_key_physically_down:
                pyautogui.keyUp(target_key)
                self.is_key_physically_down = False
        elif intensity >= 0.95:
            if not self.is_key_physically_down:
                pyautogui.keyDown(target_key)
                self.is_key_physically_down = True
        else:
            on_time = config.PWM_CYCLE_SECONDS * intensity
            now = time.time()
            time_in_cycle = (now - self.last_cycle_start) % config.PWM_CYCLE_SECONDS
            
            if time_in_cycle < on_time:
                if not self.is_key_physically_down:
                    pyautogui.keyDown(target_key)
                    self.is_key_physically_down = True
            else:
                if self.is_key_physically_down:
                    pyautogui.keyUp(target_key)
                    self.is_key_physically_down = False

    def update_pedals(self, new_pedal):
        """Handles gas and brake pedal logic."""
        if new_pedal != self.current_pedal_state:
            if self.current_pedal_state == 'gas': pyautogui.keyUp(config.KEY_UP)
            if self.current_pedal_state == 'brake': pyautogui.keyUp(config.KEY_DOWN)
            if new_pedal == 'gas': pyautogui.keyDown(config.KEY_UP)
            if new_pedal == 'brake': pyautogui.keyDown(config.KEY_DOWN)
            self.current_pedal_state = new_pedal
        
        return "GAS" if self.current_pedal_state == 'gas' else ("BRAKE" if self.current_pedal_state == 'brake' else "COAST")

    def stop(self):
        """Releases all keys."""
        pyautogui.keyUp(config.KEY_LEFT)
        pyautogui.keyUp(config.KEY_RIGHT)
        pyautogui.keyUp(config.KEY_UP)
        pyautogui.keyUp(config.KEY_DOWN)
