# Capstone Final Project


## 🌾 Linda Shamba: AI Wildlife Detection System

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
Create a file called `.env` in your repo:

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
- ✅ Saves detections to MongoDB
- ✅ Sends SMS alerts on detection
- ✅ Accurate visual logs and feedback from multiple users
- ✅ Responsive across devices (desktop/tablet/mobile)

## 🎥 Demo Video (5 Minutes)
### [Video](https://www.youtube.com/watch?v=zgM-RigtkHg)
## 🌍 Live Deployment

### *Coming soon..............*

## 📊 Screenshot Highlights


  ![Image](https://github.com/user-attachments/assets/5b082bb7-eacc-4d70-99be-bbc0f7e29a9c)
  

  <img width="1345" height="629" alt="Image" src="https://github.com/user-attachments/assets/084c12ce-b220-424e-b35c-71da43e2a80c" />

  <img width="1349" height="631" alt="Image" src="https://github.com/user-attachments/assets/361369ec-0f2b-4e63-a4be-fa7254d9c349" />

  <img width="1327" height="552" alt="Image" src="https://github.com/user-attachments/assets/fad07cea-f30e-4ec2-909d-57a78bbc0a9f" />

  <img width="1353" height="560" alt="Image" src="https://github.com/user-attachments/assets/8dcf04a9-feec-44c9-9cda-bac49eabe041" />
<img width="1342" height="560" alt="Image" src="https://github.com/user-attachments/assets/712af357-a9f4-466c-b57e-8a347dcc119f" />
<img width="1349" height="555" alt="Image" src="https://github.com/user-attachments/assets/a295be83-d6e7-4f6b-af80-bf8d6870017c" />
  
## 🔍 Analysis of Results

- The system met some of its core objective of detecting animals like elephants, monkeys, and buffaloes with over 75% confidence. 
- The use of **ModelCheckpoint** during training ensured that only the best-performing model was saved.
- SMS alerts were successfully triggered for high-confidence detections, and all activities were stored in MongoDB.
-  Overall, the system achieved its goals of wildlife detection, alerting, and farmer engagement as outlined in the project proposal.

## 🗣️ Discussion of Milestones & Impact
- Each milestone contributed critically to the system's functionality.
- Early integration of Flask and MongoDB allowed us to track and store real detections.
- Adding Twilio SMS expanded the impact by notifying farmers even without smartphones.
- The system’s ability to scale and adapt shows potential for practical deployment in regions affected by human-wildlife conflict.
-  Through this project, I learned the importance of iterative testing, threshold tuning, and user-centered design in building systems for real-world challenges.

## 🛠️ Technologies Used

- **Flask** – Python Web Framework
- **TensorFlow** – Model loading & prediction
- **MongoDB Atlas** – Database
- **Twilio API** – SMS delivery
- **HTML/CSS/JS** – Frontend

## 📌 Future Work

- 🎯 Add support for more animals
- 📱 Build mobile app version
- 📡 Add voice alert support
- 🧠 Improve model with more diverse dataset

