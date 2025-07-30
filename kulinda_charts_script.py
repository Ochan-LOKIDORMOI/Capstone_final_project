import matplotlib.pyplot as plt
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load .env and connect
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client.kulinda
detections = db.detections

# Fetch and load data
data = list(detections.find({}))
df = pd.DataFrame(data)
print("Fields loaded:", df.columns)

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
df['date'] = df['timestamp'].dt.date

# === Chart 1: Detection Confidence Over Time ===
df_sorted = df.sort_values('timestamp')
plt.figure()
plt.plot(df_sorted['timestamp'], df_sorted['confidence'], marker='o')
plt.title('Detection Confidence Over Time')
plt.xlabel('Time')
plt.ylabel('Confidence (%)')
plt.grid(True)
plt.tight_layout()
plt.savefig("chart1_confidence_over_time.png")

# === Chart 2: Number of Detections Per Species (field: label) ===
plt.figure()
df['label'].value_counts().plot(kind='bar', color='orange')
plt.title('Number of Detections per Animal')
plt.xlabel('Animal')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig("chart2_detections_per_species.png")

# === Chart 3: Alerts Sent Per Day (based on available phones) ===
df_alerted = df[df['farmer_phone'].notnull()]
alerts_per_day = df_alerted.groupby('date').size()
plt.figure()
alerts_per_day.plot(kind='bar', color='green')
plt.title('Alerts Sent Per Day')
plt.xlabel('Date')
plt.ylabel('Alerts Sent')
plt.tight_layout()
plt.savefig("chart3_alerts_per_day.png")

# === Chart 4: User Engagement (Total Detections) ===
detections_per_day = df.groupby('date').size()
plt.figure()
detections_per_day.plot(marker='o', linestyle='--', color='purple')
plt.title('User Engagement Over Time')
plt.xlabel('Date')
plt.ylabel('Detections')
plt.tight_layout()
plt.savefig("chart4_user_engagement.png")

print("✅ All charts created successfully.")