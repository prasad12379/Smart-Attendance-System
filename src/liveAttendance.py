import face_recognition
import cv2
import pickle
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import os

# Load Encodings
with open("model/encoding.pkl", "rb") as f:
    data = pickle.load(f)

known_names = []
known_encodings = []

for name, encoding in data:
    known_names.append(name)
    known_encodings.append(np.array(encoding))

# Attendance File Setup
attendance_file = "attendance.csv"
if os.path.exists(attendance_file):
    df = pd.read_csv(attendance_file)
    df["Time"] = pd.to_datetime(df["Time"])
else:
    df = pd.DataFrame(columns=["Roll Number", "Time"])

# Webcam
cap = cv2.VideoCapture(0)
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

            user_records = df[df["Roll Number"] == name]
            allow_new_entry = True

            if not user_records.empty:
                last_time = user_records["Time"].max()
                if now - last_time < timedelta(minutes=40):
                    allow_new_entry = False

            if allow_new_entry:
                new_entry = pd.DataFrame([[name, now]], columns=["Roll Number", "Time"])
                df = pd.concat([df, new_entry], ignore_index=True)
                df.to_csv(attendance_file, index=False)
                print(f"[ATTENDANCE] {name} marked at {now.strftime('%Y-%m-%d %H:%M:%S')}")

            # Draw box & label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.imshow("Live Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
