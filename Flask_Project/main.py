from flask import Flask, render_template, redirect, url_for, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Raspberry Pi IP and Port
PI_IP = "http://192.168.1.35" 
PI_PORT = ":5000"

# Directory to save images
IMAGES_DIR = os.path.join(os.getcwd(), "images")

# Ensure the 'images' folder exists
os.makedirs(IMAGES_DIR, exist_ok=True)

@app.route('/')
def index():
    stream_url = f"{PI_IP}{PI_PORT}/live"
    return render_template('index.html', stream_url=stream_url)

@app.route('/take_picture', methods=['GET'])
def take_picture():
    """Request the Raspberry Pi to take a picture and save it locally."""
    try:
        # Send a POST request to the Raspberry Pi's /take_picture endpoint
        response = requests.post(f"{PI_IP}{PI_PORT}/take_picture")

        if response.status_code == 200:
            # Generate a unique filename using the current timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            image_name = f"image_{timestamp}.jpg"
            image_path = os.path.join(IMAGES_DIR, image_name)

            # Save the image data received in the response
            with open(image_path, 'wb') as image_file:
                image_file.write(response.content)

            print(f"Image saved at {image_path}")
            return jsonify({"success": True, "image_name": image_name})
        else:
            return jsonify({"success": False, "error": f"Error {response.status_code}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
