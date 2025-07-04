import face_recognition
import cv2
import pickle
import numpy as np
from datetime import datetime
import pandas as pd
import os

# Load Encodings
with open("C:\\Users\\ADITYA JADHAV\\OneDrive\\Desktop\\ML Projects\\Face_Attendance_System\\model\\encodings.pkl", "rb") as f:
    data = pickle.load(f)

known_encodings = [np.array(enc) for enc in data["encodings"]]
known_names = data["names"]

attendance_file = "attendance.csv"
if not os.path.exists(attendance_file):
    df = pd.DataFrame(columns=["Roll Number", "Time"])
    df.to_csv(attendance_file, index=False)

cap = cv2.VideoCapture(1)
print("[INFO] Webcam started. Press 'q' to quit.")

marked = set()

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
            if name not in marked:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df = pd.read_csv(attendance_file)

                if name not in df["Roll Number"].values and now not in df["Time"].values:
                    df.loc[len(df)] = {"Roll Number": name, "Time": now}
                    df.to_csv(attendance_file, index=False)

                else:
                    continue

                    # Add new entry to the DataFrame
                
                
                
                marked.add(name)
                print(f"[ATTENDANCE] {name} marked at {now}")

                

            # Draw box & name
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    cv2.imshow("Live Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
