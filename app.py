from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import base64
import re
import io
import csv
import os
import threading
import numpy as np
from PIL import Image, ImageEnhance
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta
from flask import Response
import tensorflow as tf
from twilio.rest import Client
from flask_bcrypt import Bcrypt

app = Flask(__name__)
load_dotenv()

# === Load Model ===
MODEL_PATH = 'model/model2.h5'
model = tf.keras.models.load_model(MODEL_PATH)
app.secret_key = os.getenv("SECRET_KEY")

# === MongoDB Setup ===
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
bcrypt = Bcrypt(app)
db = client.kulinda
detections_col = db.detections
farmers_col = db.farmers
feedback_col = db.feedback
users_col = db.users

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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if users_col.find_one({"email": email}):
            return "Email already registered", 400
        if password != confirm_password:
            return "Passwords do not match", 400

        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')

        user = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "photo": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        users_col.insert_one(user)

        return redirect("/login")

    return render_template("auth_register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = users_col.find_one({"email": email})
        if not user:
            flash("❌ Email not found. Please register first.", "error")
            return redirect("/login")

        if not bcrypt.check_password_hash(user["password"], password):
            flash("❌ Incorrect password. Please try again.", "error")
            return redirect("/login")

        session["user_email"] = user["email"]
        session["user_name"] = user["name"]
        return redirect("/dashboard")

    return render_template("auth_login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out successfully.", "success")
    return redirect("/login")


@app.route('/dashboard')
def dashboard():
    if "user_email" not in session:
        return redirect("/login")

    logs = list(detections_col.find().sort("timestamp", -1).limit(5))
    total = detections_col.count_documents({})
    confidences = [float(log.get("confidence", 0))
                   for log in logs if "confidence" in log]
    accuracy = round(sum(confidences) / len(confidences),
                     2) if confidences else 0
    feedbacks = list(feedback_col.find().sort("submitted_on", -1).limit(2))

    farmer_registered = farmers_col.find_one(
        {"user_email": session["user_email"]}) is not None

    return render_template("dashboard.html", logs=logs, feedbacks=feedbacks, stats={
        "total": total, "alerts": total, "accuracy": accuracy
    }, farmer_registered=farmer_registered)


@app.route('/detect')
def detect():
    return render_template('detect.html')


@app.route('/upload')
def upload():
    return render_template("upload.html")


@app.route('/register-farmer', methods=['GET', 'POST'])
def register_farmer():
    if "user_email" not in session:
        return redirect("/login")

    user_email = session['user_email']

    if request.method == 'POST':
        # Prevent duplicate registration on submit
        if farmers_col.find_one({"user_email": user_email}):
            flash("❌ You are already registered as a farmer.", "error")
            return redirect("/profile")

        phone = request.form['phone'].strip()
        if farmers_col.find_one({"phone": phone}):
            return render_template("register.html", error="❌ This phone number is already registered.")

        farmer = {
            "name": request.form['name'].strip(),
            "phone": phone,
            "email": request.form.get('email', '').strip(),
            "location": request.form['location'].strip(),
            "photo": None,
            "registered_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_email": user_email
        }

        farmers_col.insert_one(farmer)
        session['farmer_phone'] = farmer['phone']
        flash("✅ Farmer registered successfully!", "success")
        return redirect("/profile")

    # On GET: always show form
    return render_template("register.html")


@app.route("/profile")
def profile():
    if "user_email" not in session:
        return redirect("/login")

    user_email = session["user_email"]

    # Check if user has registered as a farmer
    farmer = farmers_col.find_one({"user_email": user_email})
    if farmer:
        # Use farmer info if available
        return render_template("profile.html",
                               _id=str(farmer.get("_id")),
                               name=farmer.get("name", ""),
                               phone=farmer.get("phone", ""),
                               email=farmer.get("email", ""),
                               location=farmer.get("location", ""),
                               photo=farmer.get("photo"))
    else:
        # Otherwise fallback to basic user info
        user = users_col.find_one({"email": user_email})
        if not user:
            return redirect("/login")

        return render_template("profile.html",
                               _id=str(user.get("_id")),
                               name=user.get("name", ""),
                               phone=user.get("phone", ""),
                               email=user.get("email", ""),
                               location=user.get("location", ""),
                               photo=user.get("photo"))


@app.route('/update-profile', methods=["POST"])
def update_profile():
    if "user_email" not in session:
        return redirect("/login")

    user_email = session["user_email"]
    updates = {k: v.strip() for k, v in request.form.items()
               if k in ['name', 'email', 'phone', 'location'] and v.strip()}

    file = request.files.get("avatar")
    if file and file.filename:
        updates["photo"] = "data:image/jpeg;base64," + \
            base64.b64encode(file.read()).decode("utf-8")

    # Update users collection
    users_col.update_one({"email": user_email}, {"$set": updates})

    # If user is a farmer, also update farmers collection
    farmers_col.update_one({"user_email": user_email}, {"$set": updates})

    if "name" in updates:
        session["user_name"] = updates["name"]
    if "email" in updates:
        session["user_email"] = updates["email"]

    flash("✅ Profile updated successfully", "success")
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
        # 🔄 1. Parse incoming base64 image
        data = request.get_json()
        image_data = data['image']
        img_bytes = base64.b64decode(
            re.sub('^data:image/.+;base64,', '', image_data))

        # 🧼 2. Preprocess the image
        img_array = preprocess_image(img_bytes)

        # 🤖 3. Run prediction
        preds = model.predict(img_array)[0]
        class_names = ['Elephant', 'Monkey', 'Buffalo']
        max_index = int(np.argmax(preds))
        confidence = float(np.max(preds)) * 100

        # 🛑 4. Skip low-confidence predictions
        if confidence < 75:
            return jsonify({})  # Do not log or alert

        label = class_names[max_index]

        # 📍 5. Fetch latest farmer info
        latest_farmer = farmers_col.find_one(sort=[("registered_on", -1)])
        phone = latest_farmer.get("phone") if latest_farmer else None
        location = latest_farmer.get(
            "location") if latest_farmer else "Unknown"
        name = latest_farmer.get("name") if latest_farmer else "Farmer"

        # 🧾 6. Prepare result
        result = {
            "label": label,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "location": location,
            "image": image_data,
            "farmer_phone": phone
        }

        # 🗃️ 7. Insert into MongoDB
        insert_result = detections_col.insert_one(result)
        result["_id"] = str(insert_result.inserted_id)

        # 📲 8. Send SMS in background
        if phone:
            def sms_job():
                formatted_phone = phone.strip()
                if formatted_phone.startswith("0"):
                    formatted_phone = "+250" + formatted_phone[1:]
                elif not formatted_phone.startswith("+"):
                    formatted_phone = "+250" + formatted_phone

                try:
                    send_sms_real(
                        formatted_phone,
                        f"LINDA ALERT 🚨\n"
                        f"Hi {name},\n"
                        f"{label} has been detected on your farm in {location}.\n"
                        f"The deterrent has been activated."
                    )
                except Exception as sms_err:
                    print("❌ SMS Error:", sms_err)

            threading.Thread(target=sms_job).start()

        # ✅ 9. Return prediction result
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
