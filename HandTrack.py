import mediapipe as mp
import cv2 as cv
import pyautogui

# Disable the pause
pyautogui.PAUSE = 0
#I need optimisation
import numpy as np
import cProfile

import threading
import sounddevice as sd
import numpy as np


from mouse_cursor_manager import MouseCursorManager

import sounddevice as sd
from scipy.io.wavfile import read


lock_click = threading.Lock()
lock_unclick = threading.Lock()
FP_CLICK = "click.wav"
fs0, data0 = read(FP_CLICK)
FP_UNCLICK = "unclick.wav"
fs1, data1 = read(FP_UNCLICK)


# Set the maximum number of allowed threads
#I'm in tears this might be unnecessary but for some reasing i feel like sd is randomly locking up if too many plays
#are called on it, even if its non blocking
max_click_threads = 1
semaphore_click = threading.Semaphore(max_click_threads)
max_unclick_threads = 1
semaphore_unclick = threading.Semaphore(max_unclick_threads)

def PLAY_ONE_SHOT_CLICK():
    print("U")
    if not semaphore_click.acquire(blocking=False):
        # Exit the thread if unable to acquire the semaphore
        return
    try:
        print("Hereertghgreghgtr")
        sd.play(data0, fs0, blocking=False)
    finally:
        semaphore_click.release()

def PLAY_ONE_SHOT_UNCLICK():
    if not semaphore_unclick.acquire(blocking=False):
        # Exit the thread if unable to acquire the semaphore
        return
    try:
        sd.play(data1, fs1, blocking=True)
    finally:
        semaphore_unclick.release()
# Replace these values with your screen's pixel height and width
SCREEN_HEIGHT = 1080
SCREEN_WIDTH = 1920

# Define the size of the moving average window
MOVING_AVERAGE_WINDOW_SIZE = 2

# Global variable to store the window size for the moving average
DIST_FINGER_THUMB_WINDOW_SIZE = 2
# Initialize an empty list to store the past coordinates
past_coordinates_window = []

# Define the weight for lerp (you can adjust this for different levels of smoothness)
LERP_WEIGHT = 0.5  # Smooth Follow. More = more instant
ALPHA = 0.8  # Smoothing factor, adjust as needed # Anti-Jittering # Less = older values more weight
# Define a threshold for outlier rejection
OUTLIER_THRESHOLD = 50  # Adjust as needed based on your setup

# Initialize the previous mouse position
prev_mouse_position = pyautogui.position()





x_scaler=3.0
y_scaler=3.0
def remap_to_pixel_coordinates(x, y):
    # Scale the input coordinates
    #x, y originally range from 0..1
    x_scaled=(x-0.5)*x_scaler
    y_scaled=(y-0.5)*y_scaler

    x_scaled+=0.5
    y_scaled+=0.5

    # Assuming SCREEN_WIDTH and SCREEN_HEIGHT are defined somewhere
    pixel_x = min(max(int(x_scaled * SCREEN_WIDTH), 0), SCREEN_WIDTH - 1)
    pixel_y = min(max(int(y_scaled * SCREEN_HEIGHT), 0), SCREEN_HEIGHT - 1)
    
    return pixel_x, pixel_y

DISABLE_PYAUTOGUI_MOUSE_MOVE= False
def safe_pyautogui_function(func, *args, **kwargs):
    global DISABLE_PYAUTOGUI_MOUSE_MOVE
    """
    Wrapper function for pyautogui functions to check the pyautogui_enabled flag.
    """
    if not DISABLE_PYAUTOGUI_MOUSE_MOVE:
        func(*args, **kwargs)

def DISABLE_MOUSE_MOVE():
    global DISABLE_PYAUTOGUI_MOUSE_MOVE
    if not DISABLE_PYAUTOGUI_MOUSE_MOVE:
        DISABLE_PYAUTOGUI_MOUSE_MOVE=True
def ENABLE_MOUSE_MOVE():
    global DISABLE_PYAUTOGUI_MOUSE_MOVE
    if DISABLE_PYAUTOGUI_MOUSE_MOVE:
        DISABLE_PYAUTOGUI_MOUSE_MOVE=False


def move_mouse_lerp(x, y):
    global prev_mouse_position
    current_mouse_position = pyautogui.position()

    # Linear interpolation (lerp) between previous and current mouse positions
    new_x = (1 - LERP_WEIGHT) * prev_mouse_position[0] + LERP_WEIGHT * x
    new_y = (1 - LERP_WEIGHT) * prev_mouse_position[1] + LERP_WEIGHT * y

    safe_pyautogui_function(pyautogui.moveTo,int(new_x), int(new_y))
    prev_mouse_position = (new_x, new_y)




# Define parameters for anti-jitter function
JITTER_THRESHOLD = 30  # Radial pixel threshold within which you are jittering Threshold for detecting jitter
MIN_TO_TURN_ANTI_JITTER_OFF = 2  # Number of consecutive frames to keep anti-jitter on
MIN_TO_TURN_ANTI_JITTER_ON = 20  # Number of consecutive frames to keep anti-jitter off

# Initialize state variables for anti-jitter function
jitter_counter = 0
anti_jitter_on = False
initial_jitter_position = None

# ... (rest of your code)
# ... (rest of your code)

def anti_jitter_filter(moving_coords_window, threshold=JITTER_THRESHOLD):
    # Extract prev_coord and new_coord from the moving window
    prev_coord = np.array(moving_coords_window[0])  # Convert to NumPy array
    new_coord = np.array(moving_coords_window[-1])  # Convert to NumPy array

    global jitter_counter, anti_jitter_on, initial_jitter_position

    if initial_jitter_position is not None:

    # Check if anti-jitter is currently on
    #if anti_jitter_on:
        #print(np.linalg.norm(new_coord - initial_jitter_position))
        #pass
        # If on, increment the counter and check if it should turn off
        jitter_counter += 1
        if np.linalg.norm(new_coord - initial_jitter_position) < threshold:

            # If new_coord is within pixel error threshold of coord when first entered jitter phase

            jitter_counter = 0
        else:
            # Increment jitter counter
            jitter_counter += 1

        new_coord = initial_jitter_position
        if jitter_counter >= MIN_TO_TURN_ANTI_JITTER_OFF:
            anti_jitter_on = False
            jitter_counter = 0
            initial_jitter_position = None  # Reset initial position
        
    else:

        # If off, check if coordinates are within the threshold
        if np.linalg.norm(new_coord - prev_coord) < threshold:
            jitter_counter += 1
            # If within the threshold, check if it should turn on
            if jitter_counter >= MIN_TO_TURN_ANTI_JITTER_ON:
                anti_jitter_on = True
                jitter_counter = 0
                initial_jitter_position = new_coord  # Store the newest coord (the coord which caused it to enter this phase)
        else:
            jitter_counter = 0  # Reset counter if coordinates move outside the threshold

    # Return the filtered coordinates based on the current state
    return new_coord if anti_jitter_on else new_coord







def calculate_3d_distance(point1, point2):
    if point1 is not None and point2 is not None:
        return np.linalg.norm(np.array(point1) - np.array(point2))
    else:
        return None

def get_3d_coordinates(hand_landmarks, landmark):
    if hand_landmarks is not None and hasattr(hand_landmarks, 'landmark'):
        landmark_point = hand_landmarks.landmark[landmark]
        return (landmark_point.x, landmark_point.y, landmark_point.z)
    else:
        return None



# Function to calculate the moving window average
def moving_average(data,window_size):
    window_size = min(len(data), window_size)
    return sum(data) / window_size



# Example usage for moving average
results_history=[]

def calculatedistbetweenfingerandthumbtip(results):
    if results.multi_hand_landmarks and results.multi_hand_landmarks[0].landmark:
        hand_landmarks = results.multi_hand_landmarks[0]
        thumb_tip = get_3d_coordinates(hand_landmarks, mp.solutions.hands.HandLandmark.THUMB_TIP)
        index_finger_tip = get_3d_coordinates(hand_landmarks, mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP)

        distance = calculate_3d_distance(thumb_tip, index_finger_tip)

        if distance is not None:
            scaled_distance = distance * 100

            # Example usage for moving average
            global results_history

            # Update the results history with the current distance value
            results_history.append(scaled_distance)

            # Keep the history length within the window size
            results_history = results_history[-DIST_FINGER_THUMB_WINDOW_SIZE:]

            # Calculate the moving window average
            smoothed_distance = moving_average(results_history,DIST_FINGER_THUMB_WINDOW_SIZE)

            # Use the smoothed distance for further processing
            if smoothed_distance is not None:
                #print(f"Smoothed Distance between thumb tip and index finger tip: {smoothed_distance:.2f} units")

                # Perform additional processing if needed
                # ...

                return smoothed_distance

    return float('inf') #Cause none causes false but what if you were mouse button held down at that point
def isFingerThumbTouching(results,threshold=10):
    dist=calculatedistbetweenfingerandthumbtip(results)

    if dist is not None and dist<threshold:
        return True
    else:
        return False

def isFingerPinkyTouching(results,threshold=10):
    dist=calculatedistbetweenfingerandthumbtip(results)

    if dist is not None and dist<threshold:
        return True
    else:
        return False

def get_index_finger_coordinates(results):
    if results.multi_hand_landmarks and results.multi_hand_landmarks[0].landmark:
        hand_landmarks = results.multi_hand_landmarks[0]
        index_finger_landmark = hand_landmarks.landmark[8]
        return remap_to_pixel_coordinates(index_finger_landmark.x, index_finger_landmark.y)
    return []

IS_MOUSE_DOWN=False

cursor_manager = MouseCursorManager()
def main_loop():
    global cursor_manager;
    global IS_MOUSE_DOWN
    global past_coordinates_window, smoothed_coordinates
    while True:
        # Read a frame from the video capture
        ret, frame = vid.read()

        # Break the loop if unable to read a frame
        if not ret:
            break

        # Flip the frame horizontally (left-to-right flip)
        frame = cv.flip(frame, 1)

        # Convert the frame to RGB
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        # Process the frame with mediapipe hands
        results = mp_hands.process(rgb_frame)


        # Get index finger coordinates with pixel coordinates
        index_finger_coordinates = get_index_finger_coordinates(results)


        if isFingerThumbTouching(results, 5.0):
            if not IS_MOUSE_DOWN:
                #Using disable and enable stuff cause to actually click you need to mouse to stop so you can click
                DISABLE_MOUSE_MOVE()
                # Schedule the function to run after 5 seconds
                timer = threading.Timer(0.2, ENABLE_MOUSE_MOVE)

                # Start the timer
                timer.start()
                print("Mouse DOWN")
                pyautogui.mouseDown()

                threading.Thread(target=PLAY_ONE_SHOT_CLICK).start()

                IS_MOUSE_DOWN = True
        else:
            if IS_MOUSE_DOWN:
                ENABLE_MOUSE_MOVE()
                print("Mouse Up")
                pyautogui.mouseUp()
                threading.Thread(target=PLAY_ONE_SHOT_UNCLICK).start() #Says non- blocking but original funciton itself does have minisule slow down


                IS_MOUSE_DOWN = False
        # Reject outliers in the hand position data
        if index_finger_coordinates:
            cursor_manager.change_mouse_pointer(True) #Maintains prev state so you're good
            # Append the new index finger coordinates to the moving window
            past_coordinates_window.append(index_finger_coordinates)

            # Keep the moving window size within the specified limit
            past_coordinates_window = past_coordinates_window[-MOVING_AVERAGE_WINDOW_SIZE:]

            # Apply exponential moving average (EMA) to smooth the coordinates
            smoothed_coordinates = anti_jitter_filter(past_coordinates_window)


        if not index_finger_coordinates:
            cursor_manager.change_mouse_pointer(False)
            smoothed_coordinates = None

        # If hands are detected, move the mouse pointer using lerp
        if smoothed_coordinates is not None:
            move_mouse_lerp(smoothed_coordinates[0], smoothed_coordinates[1])

        # If hands are detected, impose media pose on hands in the frame
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks on the frame (you may customize the drawing as needed)
                mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, hands.HAND_CONNECTIONS)

        # Display the mapped screen pixel coordinates for the index finger on the frame
        #if smoothed_coordinates is not None:
        #    cv.putText(frame, f"Index Finger: {smoothed_coordinates[0]}, {smoothed_coordinates[1]}",
        #               (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv.LINE_AA)

        # Show the frame in an OpenCV window
        cv.imshow("Hand Tracking", frame)

        # Exit the loop if the 'Escape' key is pressed
        if cv.waitKey(1) == 27:
            break
    cursor_manager.change_mouse_pointer(False)


# Run the profiler on the main loop function
if __name__ == '__main__':
    vid = cv.VideoCapture(0)
    past_coordinates_window = []
    smoothed_coordinates = None
    hands = mp.solutions.hands

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    # Create a window
    cv.namedWindow("Hand Tracking", cv.WINDOW_NORMAL)

    cProfile.run("main_loop()", sort="cumulative")

    # Release the video capture and close the OpenCV window

    vid.release()
    cv.destroyAllWindows()
