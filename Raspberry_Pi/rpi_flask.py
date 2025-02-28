from flask import Flask, Response, jsonify, request
import cv2
import threading
import time
import os

app = Flask(__name__)

# Initialize camera
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

@app.route('/live')
def live_feed():
    """Stream live video frames."""
    def generate_frames():
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/take_picture', methods=['POST'])
def take_picture():
    """Capture an image, send it as a response, and delete it locally."""
    success, frame = camera.read()
    if not success:
        return jsonify({"error": "Failed to capture image"}), 500

    # Generate unique image name with timestamp
    timestamp = time.strftime('%Y%m%d%H%M%S')
    image_name = f"image_{timestamp}.jpg"
    image_path = os.path.join('/tmp', image_name)

    # Save the image temporarily
    cv2.imwrite(image_path, frame)

    # Send the image as a response and delete it
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        os.remove(image_path)  # Delete the image after sending
        return Response(image_data, content_type='image/jpeg')
    except Exception as e:
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 500

if __name__ == '__main__':
    ip_address = os.getenv('FLASK_RUN_HOST', '0.0.0.0')  # Default to 0.0.0.0
    app.run(host=ip_address, port=5000, threaded=True)
