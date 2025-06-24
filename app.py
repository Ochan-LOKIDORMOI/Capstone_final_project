from flask import Flask, render_template, request, jsonify, session, redirect
import base64
import re
import numpy as np
from PIL import Image
import io
import tensorflow as tf
from pymongo import MongoClient
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from flask import Response
import io
import csv
from bson import ObjectId  # Added this import
import base64

app = Flask(__name__)

# === Load .env variables ===
load_dotenv()

# === Load Model ===
MODEL_PATH = 'model/kulinda_model.h5'
model = tf.keras.models.load_model(MODEL_PATH)

# === MongoDB Setup ===
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.kulinda
detections_col = db.detections
farmers_col = db.farmers
feedback_col = db.feedback  # Added feedback collection

# === Preprocessing ===


def preprocess_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    img_array = np.array(image) / 255.0
    return np.expand_dims(img_array, axis=0)

# === SMS Sender ===


def send_sms_real(phone, message):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = os.getenv("TWILIO_PHONE")

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=message,
        from_=twilio_number,
        to=phone
    )
    return message.sid

# === ROUTES ===


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('auth_register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('auth_login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    logs = list(detections_col.find().sort("timestamp", -1).limit(5))
    total = detections_col.count_documents({})
    alerts_sent = total  # Assuming all detections = alert sent
    confidences = [float(log.get("confidence", 0))
                   for log in logs if "confidence" in log]
    accuracy = round(sum(confidences) / len(confidences),
                     2) if confidences else 0

    # Get the 2 most recent feedbacks
    feedbacks = list(db.feedback.find().sort("submitted_on", -1).limit(2))

    return render_template("dashboard.html", logs=logs, feedbacks=feedbacks, stats={
        "total": total,
        "alerts": alerts_sent,
        "accuracy": accuracy
    })


@app.route('/detect')
def detect():
    return render_template('detect.html')


@app.route('/register-farmer', methods=['GET', 'POST'])
def register_farmer():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        location = request.form['location']

        existing = db.farmers.find_one({"phone": phone})
        if existing:
            return render_template('register.html', error="Farmer with this phone already exists.")

        farmer = {
            "name": name,
            "phone": phone,
            "location": location,
            "email": "",  # Optional, can be added later
            "photo": None,
            "registered_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        db.farmers.insert_one(farmer)
        return render_template('register.html', success=True)

    return render_template('register.html', success=False)


@app.route('/sms')
def sms():
    return render_template('sms.html')


@app.route('/test-sms', methods=['POST'])
def test_sms():
    phone = request.form.get('phone')
    message = request.form.get('message')
    try:
        send_sms_real(phone, message)
        return render_template('sms.html', success="SMS sent successfully!")
    except Exception as e:
        return render_template('sms.html', error=str(e))


@app.route('/log')
def log():
    logs_cursor = detections_col.find().sort("timestamp", -1)
    logs = []
    now = datetime.now()

    for d in logs_cursor:
        # Parse timestamp
        timestamp_str = d.get("timestamp", "N/A")
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except:
            continue  # skip invalid timestamp

        # Determine view category
        view = (
            'day' if timestamp.date() == now.date()
            else 'week' if timestamp > now - timedelta(days=7)
            else 'month' if timestamp > now - timedelta(days=30)
            else 'older'
        )

        logs.append({
            "timestamp": timestamp_str,
            "label": d.get('label', 'Unknown'),
            "confidence": round(float(d.get('confidence', 0)), 2),
            "location": d.get('location', 'Unknown'),
            "view": view
        })

    total = len(logs)
    avg_confidence = round(sum(log['confidence']
                           for log in logs) / total, 2) if total else 0
    unique_animals = len(set(log['label'] for log in logs))

    stats = {
        "total": total,
        "avg_confidence": avg_confidence,
        "unique_animals": unique_animals
    }

    return render_template("log.html", logs=logs, stats=stats)


@app.route('/export-csv')
def export_csv():
    logs = list(detections_col.find().sort("timestamp", -1))
    download = request.args.get("download", "false").lower() == "true"

    def generate():
        data = io.StringIO()
        writer = csv.writer(data)

        # Write header
        writer.writerow(
            ["Timestamp", "Animal", "Confidence (%)", "Location", "Alert Status"])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # Write data rows
        for log in logs:
            timestamp = log.get("timestamp", "N/A")
            label = log.get("label", "Unknown")
            confidence = round(float(log.get("confidence", 0)), 2)
            location = log.get("location", "Unknown")
            status = "Sent"

            writer.writerow([timestamp, label, confidence, location, status])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    disposition = (
        "attachment; filename=detection_log.csv"
        if download else
        "inline; filename=detection_log.csv"
    )

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": disposition})


@app.route('/latest-detection')
def latest_detection():
    latest = detections_col.find_one(sort=[("timestamp", -1)])
    if not latest:
        return jsonify({})
    return jsonify({
        "_id": str(latest.get("_id", "")),  # Added ID field
        "label": latest.get("label", "Unknown"),
        "confidence": round(float(latest.get("confidence", 0)), 2),
        "timestamp": latest.get("timestamp", "N/A"),
        "location": latest.get("location", "Unknown"),
        "image": latest.get("image", "")
    })


@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message']
        rating = int(request.form['rating'])

        feedback_doc = {
            "name": name,
            "message": message,
            "rating": rating,
            "submitted_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        db.feedback.insert_one(feedback_doc)

    # Get all feedback to show on page
    testimonials = list(db.feedback.find().sort("submitted_on", -1).limit(5))
    return render_template('feedback.html', testimonials=testimonials)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        image_data = data['image']
        image_bytes = base64.b64decode(
            re.sub('^data:image/.+;base64,', '', image_data))
        image_array = preprocess_image(image_bytes)

        predictions = model.predict(image_array)[0]
        class_names = ['Buffalo', 'Elephant', 'Monkey']
        predicted_index = int(np.argmax(predictions))
        confidence = float(predictions[predicted_index]) * 100

        # Get the most recent farmer's details
        latest_farmer = farmers_col.find_one(sort=[("registered_on", -1)])
        location = latest_farmer.get(
            'location', 'Unknown') if latest_farmer else 'Unknown'
        phone = latest_farmer.get('phone') if latest_farmer else None

        result = {
            "_id": str(ObjectId()),  # Added unique ID
            "label": class_names[predicted_index],
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "location": location,  # Use actual farm location
            "image": image_data,
            "farmer_phone": phone
        }

        detections_col.insert_one(result)

        # Send SMS only to the detecting farmer
        if phone:
            try:
                msg = (
                    f"KULINDA SHAMBA ALERT 🚨\n"
                    f"{result['label']} detected at {location}\n"
                    f"Time: {result['timestamp']}\n"
                    f"Confidence: {result['confidence']}%"
                )
                send_sms_real(phone, msg)
            except Exception as sms_err:
                print(f"Failed to send SMS: {sms_err}")

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


# === RUN APP ===
if __name__ == '__main__':
    app.run(debug=True)
