import requests
import cv2
import time
import os
import threading
import RPi.GPIO as GPIO
import json
import numpy as np
import time as time
from hx711 import HX711
import board
import neopixel

# API Endpoint
url = "http://192.168.1.209:5000/api/process-image"
api_key = "keCnRXk6xJ5qtq3VEkb5nmiMcj2n1yCy"

# Set the directory to save images
save_dir = os.path.join(os.getcwd(), "images")  # Saves in projectfolder/images/
os.makedirs(save_dir, exist_ok=True)  # Create folder if it doesn't exist

# Initialize camera
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Raspberry Pi GPIO Button Setup
BUTTON_PIN = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set GPIO Pins
DT_PIN = 6   # GPIO6
SCK_PIN = 5  # GPIO5

# Initialize HX711
GPIO.setmode(GPIO.BCM)
hx = HX711(DT_PIN, SCK_PIN)
hx.zero()

# Set the known scale factor from previous calibration
KNOWN_SCALE_FACTOR = -1011.3961038961039  # Replace this with your actual scale factor

hx.set_scale_ratio(KNOWN_SCALE_FACTOR)

# LED Configuration
LED_PIN = board.D18
NUM_LEDS = 1
BRIGHTNESS = 0.5

# Initialize the LED
pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

previous_frame = None  # Global variable for motion detection

# Flag to control the webcam GUI
gui_running = True

def blink_red_led():
    """Blink the red LED for 5 seconds and then stop."""
    for _ in range(5):  # Blink for 5 seconds (0.5s ON, 0.5s OFF)
        pixels.fill((255, 0, 0))  # Red ON
        pixels.show()
        time.sleep(0.5)

        pixels.fill((0, 0, 0))  # OFF
        pixels.show()
        time.sleep(0.5)

def read_weight():
    """ Read weight from the load cell """
    weight = hx.get_weight_mean()
    hx.power_down()
    hx.power_up()
    return weight

def show_camera_gui():
    """Function to display webcam feed in a separate thread."""
    global gui_running

    while gui_running:
        success, frame = camera.read()
        if not success:
            print("Failed to capture image")
            break

        # Display the live webcam feed
        cv2.imshow("Webcam Feed", frame)

        # Press 'q' to exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            gui_running = False
            break

    cv2.destroyAllWindows()
    camera.release()

def detect_motion(frame, threshold=10000):
    """Detect motion by comparing frame differences."""
    global previous_frame
    if previous_frame is None:
        previous_frame = frame
        return False  # No previous frame to compare
    
    diff = cv2.absdiff(previous_frame, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    motion_score = np.sum(thresh)  # Sum of white pixels (motion detected)

    previous_frame = frame  # Update previous frame
    return motion_score > threshold  # Returns True if motion is detected

def detect_blurry(image, threshold=80):
    """Detect if an image is blurry using Laplacian variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold  # Returns True if image is blurry

def read_stable_weight():
    """Read 10 weight values, remove outliers, and return the median weight."""
    print("Scale initialized. Reading weight...")
    weight_values = [] # Array to store weight values
    
    weight = read_weight()
    input("Ready? Press Enter to continue...")
    
    print("Please wait for the weight reading")
    while len(weight_values) < 10:
        weight = read_weight()
        # to debug the weight value
        #print(f"Weight: {weight:.2f} g")
        weight_values.append(weight)
        time.sleep(1)
        
    # Sort values from small to big
    weight_values.sort()

    # Remove the smallest and largest value
    weight_values.pop(0)  # Remove smallest value
    weight_values.pop(-1) # Remove largest value

    # Take the last 5 elements
    last_five_values = weight_values[-5:]

    # Find the middle value (median)
    middle_value = np.median(last_five_values)

    print("Finish weight reading")
    print(f"Gram: {middle_value:.2f} g")
    
    return middle_value
     

def capture_and_save():
    """Capture an image, prompt user for weight, save it, and send it to the API."""
    success, frame = camera.read()
    if not success:
        print("Failed to capture image")
        return
        
    # Detect motion or blurriness
    #if detect_motion(frame):
     #   print("Red Indicator: Motion detected. Please stay still.")
      #  blink_red_led()
       # return
        
    if detect_blurry(frame):
        print("Red Indicator: Image is blurry. Please retry.")
        blink_red_led()
        return
    
    # Generate image filename with weight
    timestamp = time.strftime('%Y%m%d%H%M%S')
    image_name = f"image_{timestamp}.jpeg"
    image_path = os.path.join(save_dir, image_name)

    # Save the image
    cv2.imwrite(image_path, frame)
    print(f"Picture saved as {image_path}")

    # Get stable weight measurement
    middle_value = read_stable_weight()

    # Send the captured image to the API
    send_to_api(image_path, middle_value)

def send_to_api(image_path, weight):
    """Upload the captured image to the API with the specified weight."""
    print("Uploading image and weight to API...")

    try:
        files = {"image": open(image_path, "rb")}
        data = {"mass": str(weight)}  # Convert weight to string
        headers = {"X-API-Key": api_key}

        # Send API request
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)

        # Parse and print JSON response
        json_data = response.json()
        print("\nAPI Response:")
        print(json.dumps(json_data, indent=4))  # Pretty-print JSON

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")

def monitor_button():
    """Continuously monitor the button press and capture an image when pressed."""
    try:
        while True:
            time.sleep(0.1)
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Button is pressed
                print("Button is pressed, capturing image...")
                capture_and_save()
    except KeyboardInterrupt:
        GPIO.cleanup()

# Start GUI in a separate thread
gui_thread = threading.Thread(target=show_camera_gui, daemon=True)
gui_thread.start()

# Run the button monitoring in a separate thread
button_thread = threading.Thread(target=monitor_button, daemon=True)
button_thread.start()

# Wait for GUI to close before ending the program
gui_thread.join()
button_thread.join()

print("Webcam closed. Program exiting.")