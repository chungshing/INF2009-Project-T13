
# Raspberry Pi Project Setup with Breadboard, Button, HX711 Load Cell, and LED Light

This guide provides detailed instructions to set up a Raspberry Pi project using a **breadboard**, **button**, **HX711 load cell**, and **LED light**. It includes wiring details, software installation, and running the project.

---

## Prerequisites
- Raspberry Pi with Raspberry Pi OS installed
- Python 3 installed
- Breadboard
- HX711 Load Cell Module
- Load cell sensor
- LED light
- Push Button
- Jumper wires
- Ngrok account (if using mobile network access)

---

## Hardware Setup
### Wiring Diagram (HX711 to Raspberry Pi GPIO)
| **HX711 Pin** | **Raspberry Pi GPIO** |
|--------------|----------------------|
| VCC         | 5V (Pin 4)            |
| GND         | GND (Pin 6)           |
| DT          | GPIO6 (Pin 31)        |
| SCK         | GPIO5 (Pin 29)        |

### **Wiring Diagram (LED to Raspberry Pi GPIO)**
| **LED Pin** | **Raspberry Pi GPIO** |
|------------|----------------------|
| Power     | 5V (Pin 2)            |
| Ground    | GND (Pin 14)          |
| Data (DT) | GPIO18 (Pin 12)       |

### **Wiring Diagram (Breadboard to Raspberry Pi GPIO)**
| **Button Pin** | **Raspberry Pi GPIO** |
|--------------|----------------------|
| One side of Button | GPIO16 (Pin 36)|
| Other side of Button | GND (Pin 34) |

---

## Setting Up the Virtual Environment

1. Open a terminal on the Raspberry Pi.
2. Create a project directory and navigate into it:
```sh
mkdir project && cd project
```
3. Create a virtual environment named `project`:
```sh
python3 -m venv project
```
4. Activate the virtual environment:
```sh
source project/bin/activate
```
5. Install the HX711 library from GitHub:
```sh
pip3 install 'git+https://github.com/gandalf15/HX711.git#egg=HX711&subdirectory=HX711_Python3'
```
6. Install all required dependencies from `requirements.txt`:
```sh
pip install -r requirements.txt
```

---

## Running the Project

1. Open a terminal and start a root shell:
```sh
sudo bash
```
2. Activate the virtual environment inside the root shell:
```sh
source project/bin/activate
```
3. If using a mobile network, use Ngrok to expose the API:

- Download and install Ngrok if not already installed.

- Start an HTTP tunnel on port 5000:
```sh
ngrok http 5000
```
- Copy the Ngrok-provided public URL and update the API endpoint in the project code.

4. Run the project script:
```sh
python3 Intergrated_Project_Pi.py
```

---

## How It Works
- The **button press** triggers the camera to capture an image.

- The **load cell (HX711)** reads the weight and sends data to the Raspberry Pi.

- The **LED blinks** as feedback when motion is detected or an image is blurry.

- The **captured image and weight data** are sent to an API.
