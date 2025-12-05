import cv2
import time
import config
import utils
from controls import SteeringController
from vision import HandTracker

def main():
    cap = cv2.VideoCapture(0)
    
    # standard res, good balance of speed vs accuracy
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Initialize modules
    tracker = HandTracker()
    controller = SteeringController()
    
    # keep track of stuff
    current_angle = 0.0 
    
    # for calculating fps
    prev_frame_time = 0
    
    print("booting up...")
    print(f"  running at 1/{config.PROCESS_EVERY_N_FRAMES} AI rate for speed")
    print("  visuals stripped down for max fps")
    print("  sensitivity curve applied")
    print("press 'q' to kill it")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            
            # 1. Vision
            results = tracker.process(frame)

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
                raw_angle = utils.calculate_angle(l_wrist, r_wrist)
                current_angle = (config.SMOOTHING_ALPHA * raw_angle) + ((1 - config.SMOOTHING_ALPHA) * current_angle)
                
                # keep it simple - just a line and dots. drawing the whole skeleton kills fps.
                cv2.line(frame, l_wrist, r_wrist, (255, 255, 0), 2)
                cv2.circle(frame, l_wrist, 8, (0, 255, 255), -1)
                cv2.circle(frame, r_wrist, 8, (0, 255, 255), -1)
                
                # 3. Update Steering
                steering_intensity, status_text, bar_color = controller.update_steering(current_angle)

                # 4. Update Pedals
                l_fist = utils.is_fist(left_hand)
                r_fist = utils.is_fist(right_hand)
                if l_fist and r_fist: new_pedal = 'gas'
                elif not l_fist and not r_fist: new_pedal = 'brake'
                else: new_pedal = 'neutral'

                pedal_disp = controller.update_pedals(new_pedal)
                
                cv2.putText(frame, f"Pedal: {pedal_disp}", (10, h - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            else:
                controller.stop()
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
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()