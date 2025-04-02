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
url = "https://ea1d-103-30-215-142.ngrok-free.app/api/process-image"
api_key = "sRMWrC0xMWJR0ZcjKl_vnhfBe-VrKx3-FwYybAB7M_w"

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
NUM_LEDS = 12
BRIGHTNESS = 0.1

# Initialize the LED
pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

# Global variable for motion detection
previous_frame = None  

# Flag to control LED animation
led_running = False

# Flag to control the webcam GUI
gui_running = True

# Global flag to control if button should trigger capture
button_enabled = True  

def blink_red_led(index=0, blink_duration=5, blink_delay=0.5, color=(255, 0, 0)):  # Red light
    start_time = time.time()
    try:
        while time.time() - start_time < blink_duration:  # Run for blink_duration seconds
            pixels.fill((0, 0, 0))  # Turn off all LEDs
            pixels[index] = color  # Turn on selected LED in red
            pixels.show()
            time.sleep(blink_delay)  # LED stays on
            
            pixels.fill((0, 0, 0))  # Turn off LED
            pixels.show()
            time.sleep(blink_delay)  # LED stays off
    finally:
        pixels.fill((0, 0, 0))  # Ensure all LEDs are off at the end
        pixels.show()
        
# def blink_red_led():
#     """Blink the red LED for 5 seconds and then stop."""
#     for _ in range(5):  # Blink for 5 seconds (0.5s ON, 0.5s OFF)
#         pixels.fill((255, 0, 0))  # Red ON
#         pixels.show()
#         time.sleep(0.5)
# 
#         pixels.fill((0, 0, 0))  # OFF
#         pixels.show()
#         time.sleep(0.5)

def led_circle(delay=0.2, color=(255, 255, 0)):
    """Cycles through LEDs one by one until stopped."""
    global led_running
    led_running = True
    try:
        while led_running:
            for i in range(NUM_LEDS):
                if not led_running:
                    break  # Stop animation when flag is False
                pixels.fill((0, 0, 0))  # Turn off all LEDs
                pixels[i] = color  # Turn on the current LED
                pixels.show()
                time.sleep(delay)
    finally:
        pixels.fill((0, 0, 0))  # Ensure all LEDs turn off
        pixels.show()
        
def stop_led_circle():
    """Stops the LED circle animation."""
    global led_running
    led_running = False

def show_green_light(duration=5, color=(0, 255, 0)):
    """Turns all LEDs green for a specified duration, then turns them off."""
    pixels.fill(color)  # Turn all LEDs green
    pixels.show()
    time.sleep(duration)  # Wait
    pixels.fill((0, 0, 0))  # Turn off LEDs
    pixels.show()

def read_weight():
    """ Read weight from the load cell """
    weight = hx.get_weight_mean()
    hx.power_down()
    hx.power_up()
    return weight

def show_camera_gui():
    """Function to display webcam feed in a separate thread."""
    global gui_running

    # Instruction
    print("Prepare your food on the weighing scale and press the button to start")  

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
            print("Exiting program...")
            gui_running = False
            break

    # Properly close camera and windows
    camera.release()
    cv2.destroyAllWindows()

    # Cleanup GPIO to prevent issues
    GPIO.cleanup()
    
    # Exit program
    os._exit(0)

def detect_motion(frame, threshold=30000):
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

def detect_blurry(image, threshold=150):
    """Detect if an image is blurry using Laplacian variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    print(f"Variance: {variance}")
    return variance < threshold  # Returns True if image is blurry

def read_stable_weight():
    """Read 10 weight values, remove outliers, and return the median weight."""
    weight_values = [] # Array to store weight values
    
    weight = read_weight()
   
    while len(weight_values) < 10:
        weight = read_weight()
        # to debug the weight value
        print(f"Weight: {weight:.2f} g")
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
    
    global button_enabled
    button_enabled = False
    
    success, frame = camera.read()
    if not success:
        print("Failed to capture image")
        return
        
    # Detect motion or blurriness
    # if detect_motion(frame):
    #     print("Red Indicator: Motion detected. Please stay still.")
    #     button_enabled = True
    #     blink_red_led()
    #     return
        
    # if detect_blurry(frame):
    #     print("Red Indicator: Image is blurry. Please retry.")
    #     button_enabled = True
    #     blink_red_led(index=0, blink_duration=5, blink_delay=0.5)
    #     return
    
    # Generate image filename with weight
    timestamp = time.strftime('%Y%m%d%H%M%S')
    image_name = f"image_{timestamp}.jpeg"
    image_path = os.path.join(save_dir, image_name)

    # Save the image
    cv2.imwrite(image_path, frame)
    print(f"Picture saved as {image_path}")

    # Get stable weight measurement
    middle_value = read_stable_weight()
    
    #Hardcode
    image_path = "/home/user/project/images/food.jpeg"

    # Send the captured image to the API
    send_to_api(image_path, middle_value)

    # Re-enable after completion
    button_enabled = True  

def send_to_api(image_path, weight):
    """Upload the captured image to the API with the specified weight."""
    print("Uploading image and weight to API...")

    # Start LED circle animation in a separate thread
    led_thread = threading.Thread(target=led_circle, daemon=True)
    led_thread.start()

    try:
        files = {"image": open(image_path, "rb")}
        data = {"mass": str(weight)}  # Convert weight to string
        headers = {"X-API-Key": api_key}

        # Send API request
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)

        # **STOP LED CIRCLE when response is received**
        stop_led_circle()
        led_thread.join()

        # Show green light for 5 seconds
        show_green_light(duration=5)

        # Parse and print JSON response
        json_data = response.json()
        print("\nAPI Response:")
        print(json.dumps(json_data, indent=4))  # Pretty-print JSON

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        stop_led_circle()
        led_thread.join()

def monitor_button():
    """Continuously monitor the button press and capture an image when pressed."""
    global button_enabled
    try:
        while True:
            time.sleep(0.1)
            if GPIO.input(BUTTON_PIN) == GPIO.LOW and button_enabled:
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