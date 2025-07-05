import face_recognition
import cv2
import pickle
import numpy as np
from datetime import datetime, timedelta
import json
import os

# === Load Encodings ===
with open("C:\\Users\\ADITYA JADHAV\\OneDrive\\Desktop\\Smart_Attendance\\model\\encodings4.pkl", "rb") as f:
    data = pickle.load(f)

known_names = data["names"]
known_encodings = [np.array(enc) for enc in data["encodings"]]

# === Attendance File Setup ===
attendance_file = "daily_attendance.json"
if os.path.exists(attendance_file):
    with open(attendance_file, "r") as f:
        attendance_data = json.load(f)
else:
    attendance_data = {}

# === Current Date Key ===
today_date = datetime.now().strftime("%Y-%m-%d")

# === Start Webcam ===
cap = cv2.VideoCapture(1)
print("[INFO] Webcam started. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match = np.argmin(face_distances)

        if matches[best_match]:
            name = known_names[best_match]
            now = datetime.now()
            allow_new_entry = True

            # Check if already marked today
            if today_date in attendance_data:
                for rec in attendance_data[today_date]:
                    if rec["Roll Number"] == int(name):
                        last_time = datetime.strptime(rec["Time"], "%Y-%m-%d %H:%M:%S")
                        if now - last_time < timedelta(hours=24):
                            allow_new_entry = False
                            break

            if allow_new_entry:
                entry = {
                    "Roll Number": int(name),
                    "Time": now.strftime("%Y-%m-%d %H:%M:%S")
                }

                if today_date not in attendance_data:
                    attendance_data[today_date] = []

                attendance_data[today_date].append(entry)

                # Save updated JSON
                with open(attendance_file, "w") as f:
                    json.dump(attendance_data, f, indent=4)

                print(f"[ATTENDANCE] {name} marked at {entry['Time']}")

            # Draw face box and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.imshow("Live Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
