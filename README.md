# Capstone Final Project


## 🌾 Kulinda Shamba: AI Wildlife Detection System

- Linda Shamba which means "Protect the farm" is a real-time system that detects wildlife encroaching on farms.
- When an animal is detected via camera or image upload, the system sends an SMS alert to the registered farmer to take immediate action.
- The system also logs all detections in a dashboard and provides insights for analysis.

---

## 🚀 Features

- 🔍 Real-time detection via webcam
- 🖼️ Image upload detection support
- 📱 SMS alerts using Twilio
- 👨‍🌾 Farmer registration and profile management
- 📊 Detection dashboard with logs and statistics
- 💬 Feedback collection and testimonial system
- 📥 CSV export of detection logs
- 🌐 Responsive UI with sidebar nav toggle

---

## 📦 Installation & Setup

### 1 Clone the Repository
```bash
git clone https://github.com/Ochan-LOKIDORMOI/Capstone_final_project.git
cd Capstone_final_project
```
### 2 Create a virtual Environment
```bash
python -m venv name_of_environment
```
### 3 Install Requirements
```bash
pip install -r requirements.txt
```

### 4 Create ```.env``` File
```bash
Create a file called `.env.example` in your repo:

SECRET_KEY=your_secret_key
MONGO_URI=your_mongodb_uri
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE=+250xxxxxxxxx
```
- ⚠️ Don't share your .env file publicly! Use .env.example for version control.
- ✅ Add .env to .gitignore

### ▶️ Running the App
```bash
python app.py
```
Visit http://localhost:5000

## 🧪 Testing Highlights

- ✅ Detects Elephant, Monkey, Buffalo from camera and uploads

- ✅ Skips predictions under 75% confidence

- ✅ Saves detections to MongoDB

- ✅ Sends SMS alerts on detection

- ✅ Accurate visual logs and feedback from multiple users

- ✅ Responsive across devices (desktop/tablet/mobile)

## 🎥 Demo Video (5 Minutes)

## 🌍 Live Deployment

## 📊 Screenshot Highlights
- Real-time detection working on webcam
- SMS confirmation log
- Dashboard updating stats after each detection
- Profile registration, photo upload, feedback submission
- Mobile view with sidebar nav

## 🛠️ Technologies Used
- **Flask** – Python Web Framework

- **TensorFlow** – Model loading & prediction

- **MongoDB Atlas** – Database

- **Twilio API** – SMS delivery

- **HTML/CSS/JS** – Frontend

- **Render.com** – Deployment

## 📌 Future Work
- 🎯 Add support for more animals
- 📱 Build mobile app version
- 📡 Add voice alert support
- 🧠 Improve model with more diverse dataset

