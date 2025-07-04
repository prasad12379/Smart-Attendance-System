import cv2
import os
import face_recognition
import pickle

dataset_dir = "dataset"
os.makedirs(dataset_dir, exist_ok=True)

student_id = input("Enter Student Roll Number: ").strip()
student_dir = os.path.join(dataset_dir, student_id)
os.makedirs(student_dir, exist_ok=True)

cap = cv2.VideoCapture(0)
count = 0

print("[INFO] Capturing faces. Press 'q' to stop.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    face_locations = face_recognition.face_locations(frame)
    for (top, right, bottom, left) in face_locations:
        face_img = frame[top:bottom, left:right]
        path = os.path.join(student_dir, f"{student_id}_{count}.jpg")
        cv2.imwrite(path, face_img)
        count += 1
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

    cv2.imshow("Registering Face", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("[INFO] Encoding faces...")

encodings = []
names = []

for folder in os.listdir(dataset_dir):
    folder_path = os.path.join(dataset_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    for image_name in os.listdir(folder_path):
        image_path = os.path.join(folder_path, image_name)
        image = face_recognition.load_image_file(image_path)
        boxes = face_recognition.face_locations(image)
        if boxes:
            encoding = face_recognition.face_encodings(image, boxes)[0]
            encodings.append(encoding)
            names.append(folder)

data = {"encodings": encodings, "names": names}
with open("C:\\Users\\ADITYA JADHAV\\OneDrive\\Desktop\\ML Projects\\Face_Attendance_System\\model\\encodings.pkl", "wb") as f:
    pickle.dump(data, f)

print("[INFO] Registration completed.")
