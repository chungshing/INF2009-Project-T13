# Raspberry Pi Webcam Streaming with Flask

This repository provides Python scripts for setting up a **webcam streaming server** on a **Raspberry Pi** using Flask. It also includes steps to set up a Windows client to connect to the Raspberry Pi stream.

---

## Required Components

- **Raspberry Pi** (any model with a camera port or USB webcam support)
- **Raspberry Pi Camera Module** or **USB Webcam**
- **MicroSD card** with Raspberry Pi OS installed

---

## Raspberry Pi Installation

### 1. Copy the Required Files
Download the following two files from the GitHub repository and place them in a folder on your Raspberry Pi:

![image_alt](https://github.com/chungshing/INF2009-Project-T13/blob/main/Raspberry_Pi/Image/screenshot/github.PNG?raw=true)

### 2. Create a New Folder on the Raspberry Pi
Move the downloaded files into this new folder.

![image_alt](https://github.com/chungshing/INF2009-Project-T13/blob/main/Raspberry_Pi/Image/screenshot/rpi.PNG?raw=true)

### 3. Create and Activate a Virtual Environment
```bash
python3 -m venv project
source project/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Flask Application
```bash
python3 rpi_flask.py
```

---

## Windows 10 Client Setup

### 1. Clone the Repository
```bash
git clone <your-github-repo-url>
cd <your-project-folder>
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Update Raspberry Pi IP Address

- Open `main.py`
- Navigate to **line 9**
- Change the IP address to match your Raspberry Pi's IP

### 5. Run the Flask Application
```bash
python main.py
```

---
