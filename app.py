import os
import cv2
import numpy as np
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image
import threading  # For delayed deletion

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
PROCESSED_FOLDER = "static/processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER

def remove_background(input_path, output_path):
    bgr_image = cv2.imread(input_path)
    if bgr_image is None:
        raise ValueError("Invalid image file")
    
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    output_image = remove(pil_image)
    output_np = np.array(output_image)

    if output_np.shape[-1] == 4:  # RGBA Image
        r, g, b, a = cv2.split(output_np)
        result = cv2.merge([b, g, r, a])
    else:
        r, g, b = cv2.split(output_np)
        alpha = np.ones_like(r) * 255
        result = cv2.merge([b, g, r, alpha])

    cv2.imwrite(output_path, result)
    
    # Schedule deletion of uploaded image
    threading.Timer(5, lambda: os.remove(input_path) if os.path.exists(input_path) else None).start()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], os.path.splitext(filename)[0] + ".png")

    file.save(input_path)
    
    try:
        remove_background(input_path, output_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"processed_image": f"/static/processed/{os.path.basename(output_path)}"}), 200

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(app.config["PROCESSED_FOLDER"], filename)
    
    # Schedule deletion of processed image after download
    threading.Timer(10, lambda: os.remove(file_path) if os.path.exists(file_path) else None).start()

    return send_from_directory(app.config["PROCESSED_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
