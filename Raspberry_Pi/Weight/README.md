# Raspberry Pi Load Cell with HX711

This repository provides Python scripts for interfacing a **Raspberry Pi** with an **HX711 Load Cell Amplifier** to measure weight. The project includes:
- `calibrate.py`: Script to calibrate the load cell and obtain a scale factor.
- `read_weight.py`: Script to read weight using the pre-calibrated scale factor.

---

## Required Components

- **Raspberry Pi** (any model with GPIO)
- **HX711 Load Cell Amplifier**
- **Load Cell** (e.g., 5kg, 10kg, or other capacities)
- **Wires** for connections

---

## Wiring Diagram (HX711 to Raspberry Pi GPIO)

| HX711 Pin | Raspberry Pi GPIO |
|-----------|------------------|
| **VCC**   | **5V (Pin 2 or 4)**  |
| **GND**   | **GND (Pin 6)**  |
| **DT**    | **GPIO5 (Pin 29)** |
| **SCK**   | **GPIO6 (Pin 31)** |

---

## Installation

Before running the scripts, install the required library:
```bash
pip install hx711
```

---

## Step 1: Calibration (`calibrate.py`)
Run the calibration script to obtain the scale factor:
```bash
python calibrate.py
```
### **How It Works:**
1. Place a known weight (e.g., 500g) on the load cell.
2. Enter the weight when prompted.
3. The script will calculate and display a **scale factor**.
4. **Save this scale factor** for use in `read_weight.py`.

---

## Step 2: Read Weight (`read_weight.py`)
Once you have the scale factor, edit `read_weight.py` and update the following line:
```python
KNOWN_SCALE_FACTOR = <your_scale_factor>
```
Replace `<your_scale_factor>` with the value obtained from `calibrate.py`.

Then, run the script to start reading weight:
```bash
python read_weight.py
```
