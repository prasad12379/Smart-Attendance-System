import os
import pickle
import face_recognition
import numpy as np

# === Paths ===
dataset_dir = "dataset2"
encoding_file = "C:/Users/ADITYA JADHAV/OneDrive/Desktop/Smart_Attendance/model/encodings4.pkl"

# === Load existing encodings (if any) ===
if os.path.exists(encoding_file):
    with open(encoding_file, "rb") as f:
        data = pickle.load(f)
    all_encodings = data["encodings"]
    all_names = data["names"]
else:
    all_encodings = []
    all_names = []

# Convert to mutable lists
all_encodings = list(all_encodings)
all_names = list(all_names)

# === Keep track of already encoded student IDs ===
encoded_ids = set(all_names)

# === Process each student folder ===
for student_id in os.listdir(dataset_dir):
    student_path = os.path.join(dataset_dir, student_id)
    if not os.path.isdir(student_path):
        continue

    if student_id in encoded_ids:
        print(f"[SKIP] Student {student_id} already encoded.")
        continue

    print(f"[ENCODING] Student {student_id}...")

    for image_file in os.listdir(student_path):
        image_path = os.path.join(student_path, image_file)
        try:
            image = face_recognition.load_image_file(image_path)
            boxes = face_recognition.face_locations(image)
            if boxes:
                encoding = face_recognition.face_encodings(image, boxes)[0]
                all_encodings.append(encoding)
                all_names.append(student_id)
        except Exception as e:
            print(f"[ERROR] Skipping {image_path}: {e}")

# === Save updated encodings ===
data = {"encodings": all_encodings, "names": all_names}
with open(encoding_file, "wb") as f:
    pickle.dump(data, f)

print(f"[DONE] Total encodings saved: {len(all_names)}")
