import RPi.GPIO as GPIO
import numpy as np
import time as time
from hx711 import HX711 

# Set GPIO Pins
DT_PIN = 6   # GPIO6
SCK_PIN = 5  # GPIO5

# Initialize HX711
GPIO.setmode(GPIO.BCM)
hx = HX711(DT_PIN, SCK_PIN)
hx.zero()

# Set the known scale factor from previous calibration
KNOWN_SCALE_FACTOR = -1011.3961038961039 # Replace this with your actual scale factor

hx.set_scale_ratio(KNOWN_SCALE_FACTOR)

def read_weight():
    """ Read weight from the load cell """
    weight = hx.get_weight_mean()
    hx.power_down()
    hx.power_up()
    return weight

if name == "main":
    print("Scale initialized. Reading weight...")
    
    while True:
        weight = read_weight()
        print(f"Weight: {weight:.2f} g")
        time.sleep(1)