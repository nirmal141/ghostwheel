import cv2
import mediapipe as mp
import pyautogui
import math
import numpy as np
import time

# configuration
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

# set up the hand tracking
mp_hands = mp.solutions.hands

# need this to map hand pos to screen
screen_w, screen_h = pyautogui.size()

def calculate_angle(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    theta = math.atan2(y2 - y1, x2 - x1)
    return math.degrees(theta)

def is_fist(hand_landmarks):
    wrist = hand_landmarks.landmark[0]
    tips = [8, 12, 16, 20]
    folded_count = 0
    for tip_idx in tips:
        tip = hand_landmarks.landmark[tip_idx]
        pip = hand_landmarks.landmark[tip_idx - 2]
        d_tip_wrist = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
        d_pip_wrist = math.hypot(pip.x - wrist.x, pip.y - wrist.y)
        if d_tip_wrist < d_pip_wrist:
            folded_count += 1
    return folded_count >= 3

def main():
    cap = cv2.VideoCapture(0)
    
    # standard res, good balance of speed vs accuracy
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # keep track of stuff
    current_angle = 0.0 
    
    last_cycle_start = time.time()
    is_key_physically_down = False
    current_pedal_state = None 
    
    # for calculating fps
    prev_frame_time = 0
    
    # skipping frames stuff
    frame_count = 0
    last_results = None

    # use the lite model, the full one is too slow
    with mp_hands.Hands(
        model_complexity=0, 
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        max_num_hands=2) as hands:
        
        print("booting up...")
        print(f"  running at 1/{PROCESS_EVERY_N_FRAMES} AI rate for speed")
        print("  visuals stripped down for max fps")
        print("  sensitivity curve applied")
        print("press 'q' to kill it")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            # frame skipping logic
            frame_count += 1
            results = None
            
            # only run the expensive AI stuff if it's the right frame
            if frame_count % PROCESS_EVERY_N_FRAMES == 0:
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
                last_results = results # save for next frame
            else:
                # just use the old data, nobody will notice
                results = last_results

            status_text = "SEARCHING"
            bar_color = (100, 100, 100)
            steering_intensity = 0.0 

            # do something with the hand data
            if results and results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
                hand1 = results.multi_hand_landmarks[0]
                hand2 = results.multi_hand_landmarks[1]

                if hand1.landmark[0].x < hand2.landmark[0].x:
                    left_hand, right_hand = hand1, hand2
                else:
                    left_hand, right_hand = hand2, hand1

                # where are the wrists?
                l_wrist = (int(left_hand.landmark[0].x * w), int(left_hand.landmark[0].y * h))
                r_wrist = (int(right_hand.landmark[0].x * w), int(right_hand.landmark[0].y * h))

                # 2. calculate the steering angle
                raw_angle = calculate_angle(l_wrist, r_wrist)
                current_angle = (SMOOTHING_ALPHA * raw_angle) + ((1 - SMOOTHING_ALPHA) * current_angle)
                
                # keep it simple - just a line and dots. drawing the whole skeleton kills fps.
                cv2.line(frame, l_wrist, r_wrist, (255, 255, 0), 2)
                cv2.circle(frame, l_wrist, 8, (0, 255, 255), -1)
                cv2.circle(frame, r_wrist, 8, (0, 255, 255), -1)
                
                # 3. how hard are we turning?
                abs_angle = abs(current_angle)
                turn_direction = 'right' if current_angle > 0 else 'left'
                target_key = KEY_RIGHT if turn_direction == 'right' else KEY_LEFT
                opposite_key = KEY_LEFT if turn_direction == 'right' else KEY_RIGHT

                pyautogui.keyUp(opposite_key)

                if abs_angle < DEADZONE_ANGLE:
                    steering_intensity = 0.0
                    status_text = "STRAIGHT"
                    bar_color = (0, 255, 0)
                else:
                    # Calculate linear intensity (0.0 to 1.0)
                    raw_intensity = (abs_angle - DEADZONE_ANGLE) / (MAX_TURN_ANGLE - DEADZONE_ANGLE)
                    raw_intensity = min(max(raw_intensity, 0.0), 1.0)
                    
                    # magic sensitivity curve
                    # using a square root curve here makes small movements feel way more responsive.
                    # otherwise you have to turn your hands like crazy to get a reaction.
                    steering_intensity = math.pow(raw_intensity, 0.5)
                    
                    status_text = f"{turn_direction.upper()} {int(steering_intensity * 100)}%"
                    bar_color = (0, int(255 * (1-steering_intensity)), int(255 * steering_intensity))

                # 4. the pwm magic (faking analog stick)
                if steering_intensity == 0:
                    if is_key_physically_down:
                        pyautogui.keyUp(target_key)
                        is_key_physically_down = False
                elif steering_intensity >= 0.95:
                    if not is_key_physically_down:
                        pyautogui.keyDown(target_key)
                        is_key_physically_down = True
                else:
                    on_time = PWM_CYCLE_SECONDS * steering_intensity
                    now = time.time()
                    time_in_cycle = (now - last_cycle_start) % PWM_CYCLE_SECONDS
                    
                    if time_in_cycle < on_time:
                        if not is_key_physically_down:
                            pyautogui.keyDown(target_key)
                            is_key_physically_down = True
                    else:
                        if is_key_physically_down:
                            pyautogui.keyUp(target_key)
                            is_key_physically_down = False

                # 5. pedals (fists = gas)
                l_fist = is_fist(left_hand)
                r_fist = is_fist(right_hand)
                if l_fist and r_fist: new_pedal = 'gas'
                elif not l_fist and not r_fist: new_pedal = 'brake'
                else: new_pedal = 'neutral'

                if new_pedal != current_pedal_state:
                    if current_pedal_state == 'gas': pyautogui.keyUp(KEY_UP)
                    if current_pedal_state == 'brake': pyautogui.keyUp(KEY_DOWN)
                    if new_pedal == 'gas': pyautogui.keyDown(KEY_UP)
                    if new_pedal == 'brake': pyautogui.keyDown(KEY_DOWN)
                    current_pedal_state = new_pedal

                pedal_disp = "GAS" if current_pedal_state == 'gas' else ("BRAKE" if current_pedal_state == 'brake' else "COAST")
                cv2.putText(frame, f"Pedal: {pedal_disp}", (10, h - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            else:
                pyautogui.keyUp(KEY_LEFT)
                pyautogui.keyUp(KEY_RIGHT)
                pyautogui.keyUp(KEY_UP)
                pyautogui.keyUp(KEY_DOWN)
                steering_intensity = 0
                status_text = "NO HANDS"

            # draw the cool bars
            bar_width = int(steering_intensity * 200)
            cv2.rectangle(frame, (10, h - 90), (10 + bar_width, h - 70), bar_color, -1)
            cv2.rectangle(frame, (10, h - 90), (210, h - 70), (255, 255, 255), 2)
            cv2.putText(frame, f"{status_text}", (220, h - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bar_color, 2)
            
            # show fps
            new_frame_time = time.time()
            if new_frame_time - prev_frame_time > 0:
                fps = 1 / (new_frame_time - prev_frame_time)
            else:
                fps = 0
            prev_frame_time = new_frame_time
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # render it
            cv2.imshow('High-Perf Driver', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()