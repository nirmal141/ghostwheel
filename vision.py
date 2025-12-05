import mediapipe as mp
import cv2
import config

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            model_complexity=0, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=2
        )
        self.frame_count = 0
        self.last_results = None

    def process(self, frame):
        """
        Processes the frame to detect hands.
        Implements frame skipping for performance.
        """
        self.frame_count += 1
        results = None
        
        # only run the expensive AI stuff if it's the right frame
        if self.frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = self.hands.process(image)
            self.last_results = results # save for next frame
        else:
            # just use the old data, nobody will notice
            results = self.last_results
            
        return results

    def close(self):
        self.hands.close()
