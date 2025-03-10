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

def calibrate(scale_factor=None):
    """ Calibrate with a known weight """
    hx.reset()

    if scale_factor is None:
        print("Place a known weight on the scale and enter its value (grams):")
        input_weight = float(input("Known Weight (g): "))
        print("Measuring...")

        raw_value = hx.get_data_mean(readings=100)
        scale_factor = raw_value / input_weight
        print(f"Calibration complete! Scale factor: {scale_factor}")

    hx.set_scale_ratio(scale_factor)
    return scale_factor

def read_weight():
    """ Read weight from the load cell """
    weight = hx.get_weight_mean() 
    hx.power_down()
    hx.power_up()
    return weight

if name == "main":
    print("Calibrating...")
    scale_factor = calibrate()
    
    while True:
        weight = read_weight()
        print(f"Weight: {weight:.2f} g")
        time.sleep(1)