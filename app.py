from flask import Flask, render_template, request, jsonify, redirect, session
import base64
import re
import io
import csv
import os
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
from flask import Response
import tensorflow as tf
from twilio.rest import Client

app = Flask(__name__)
load_dotenv()

# === Load Model ===
MODEL_PATH = 'model/model2.h5'
model = tf.keras.models.load_model(MODEL_PATH)
app.secret_key = os.getenv("SECRET_KEY")

# === MongoDB Setup ===
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.kulinda
detections_col = db.detections
farmers_col = db.farmers
feedback_col = db.feedback

# === Preprocess Image ===


def preprocess_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    return np.expand_dims(np.array(image) / 255.0, axis=0)

# === SMS ===


def send_sms_real(phone, message):
    client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    return client.messages.create(body=message, from_=os.getenv("TWILIO_PHONE"), to=phone).sid

# === Routes ===


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/signup')
def signup():
    return render_template('auth_register.html')


@app.route('/login')
def login():
    return render_template('auth_login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    logs = list(detections_col.find().sort("timestamp", -1).limit(5))
    total = detections_col.count_documents({})
    confidences = [float(log.get("confidence", 0))
                   for log in logs if "confidence" in log]
    accuracy = round(sum(confidences) / len(confidences),
                     2) if confidences else 0
    feedbacks = list(feedback_col.find().sort("submitted_on", -1).limit(2))
    return render_template("dashboard.html", logs=logs, feedbacks=feedbacks, stats={
        "total": total, "alerts": total, "accuracy": accuracy
    })


@app.route('/detect')
def detect():
    return render_template('detect.html')


@app.route('/upload')
def upload():
    return render_template("upload.html")


@app.route('/register-farmer', methods=['GET', 'POST'])
def register_farmer():
    if request.method == 'POST':
        farmer = {
            "name": request.form['name'],
            "phone": request.form['phone'],
            "email": request.form.get('email', ''),
            "location": request.form['location'],
            "photo": None,
            "registered_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        result = farmers_col.insert_one(farmer)
        session['farmer_phone'] = farmer['phone']  # Track with phone number
        return redirect("/profile")
    return render_template("register.html")


@app.route("/profile")
def profile():
    phone = session.get("farmer_phone")
    if not phone:
        return "No farmer in session", 403

    farmer = farmers_col.find_one({"phone": phone})
    if not farmer:
        return "Farmer not found", 404

    return render_template("profile.html",
                           _id=str(farmer.get("_id")),
                           name=farmer.get("name", ""),
                           phone=farmer.get("phone", ""),
                           email=farmer.get("email", ""),
                           location=farmer.get("location", ""),
                           photo=farmer.get("photo"))


@app.route('/update-profile', methods=["POST"])
def update_profile():
    phone = session.get("farmer_phone")
    if not phone:
        return "Missing session phone", 403

    # Safely extract and filter updated values
    updates = {k: v for k, v in request.form.items()
               if k in ['name', 'email', 'phone', 'location'] and v.strip()}

    # Handle optional profile picture update
    file = request.files.get("avatar")
    if file and file.filename:
        updates["photo"] = "data:image/jpeg;base64," + \
            base64.b64encode(file.read()).decode("utf-8")

    # Perform the update
    farmers_col.update_one({"phone": phone}, {"$set": updates})

    # If phone number changed, update session
    if "phone" in updates:
        session["farmer_phone"] = updates["phone"]

    return redirect("/profile")


@app.route('/sms')
def sms():
    return render_template('sms.html')


@app.route('/test-sms', methods=['POST'])
def test_sms():
    try:
        send_sms_real(request.form['phone'], request.form['message'])
        return render_template('sms.html', success="SMS sent successfully!")
    except Exception as e:
        return render_template('sms.html', error=str(e))


@app.route('/log')
def log():
    now = datetime.now()
    logs_cursor = detections_col.find().sort("timestamp", -1).limit(100)

    formatted = []
    for d in logs_cursor:
        timestamp_str = d.get("timestamp")
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue  # skip if timestamp is invalid

        view = (
            'day' if timestamp.date() == now.date()
            else 'week' if timestamp > now - timedelta(days=7)
            else 'month' if timestamp > now - timedelta(days=30)
            else 'older'
        )

        formatted.append({
            "timestamp": timestamp_str,
            "label": d.get("label", "Unknown"),
            "confidence": round(float(d.get("confidence", 0)), 2),
            "location": d.get("location", "Unknown"),
            "view": view
        })

    total = len(formatted)
    avg_confidence = round(sum(l["confidence"]
                           for l in formatted)/total, 2) if total else 0
    unique_animals = len(set(l["label"] for l in formatted))

    return render_template("log.html", logs=formatted, stats={
        "total": total,
        "avg_confidence": avg_confidence,
        "unique_animals": unique_animals
    })


@app.route('/export-csv')
def export_csv():
    logs = list(detections_col.find().sort("timestamp", -1))
    download = request.args.get("download", "false") == "true"

    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(
            ["Timestamp", "Animal", "Confidence", "Location", "Alert"])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for log in logs:
            writer.writerow([log.get("timestamp"), log.get("label", "Unknown"),
                             round(float(log.get("confidence", 0)), 2),
                             log.get("location", "Unknown"), "Sent"])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
    return Response(generate(), mimetype='text/csv', headers={
        "Content-Disposition": "attachment; filename=detection_log.csv" if download else "inline"
    })


@app.route('/latest-detection')
def latest_detection():
    latest = detections_col.find_one(sort=[("timestamp", -1)])
    if not latest:
        return jsonify({})
    return jsonify({
        "_id": str(latest["_id"]),
        "label": latest.get("label", "Unknown"),
        "confidence": round(float(latest.get("confidence", 0)), 2),
        "timestamp": latest.get("timestamp"),
        "location": latest.get("location", "Unknown"),
        "image": latest.get("image", "")
    })


@app.route('/feedback', methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        feedback_col.insert_one({
            "name": request.form["name"],
            "message": request.form["message"],
            "rating": int(request.form["rating"]),
            "submitted_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    return render_template("feedback.html", testimonials=list(feedback_col.find().sort("submitted_on", -1).limit(5)))


@app.route('/predict', methods=["POST"])
def predict():
    try:
        data = request.get_json()
        image_data = data['image']
        img_bytes = base64.b64decode(
            re.sub('^data:image/.+;base64,', '', image_data))
        img_array = preprocess_image(img_bytes)

        preds = model.predict(img_array)[0]
        class_names = ['Elephant', 'Monkey', 'Buffalo']
        label = class_names[int(np.argmax(preds))]
        confidence = float(np.max(preds)) * 100

        latest_farmer = farmers_col.find_one(sort=[("registered_on", -1)])
        phone = latest_farmer.get("phone") if latest_farmer else None
        location = latest_farmer.get(
            "location") if latest_farmer else "Unknown"

        result = {
            "label": label,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "location": location,
            "image": image_data,
            "farmer_phone": phone
        }

        # Insert into MongoDB and attach _id
        insert_result = detections_col.insert_one(result)
        result["_id"] = str(insert_result.inserted_id)

        # ✅ Send SMS to the farmer if phone is present
        if phone:
            formatted_phone = phone.strip()
            if formatted_phone.startswith("0"):
                formatted_phone = "+250" + \
                    formatted_phone[1:]  # assumes Rwanda
            elif not formatted_phone.startswith("+"):
                formatted_phone = "+250" + formatted_phone  # fallback

            try:
                send_sms_real(
                    formatted_phone,
                    f"KULINDA SHAMBA ALERT 🚨\n"
                    f"{label} detected at {location}\n"
                    f"Confidence: {result['confidence']}%"
                )
            except Exception as sms_err:
                print("❌ SMS Error:", sms_err)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
