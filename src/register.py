import cv2
import os
import face_recognition
import threading
import queue
import pickle

# Constants
CAPTURE_COUNT = 30
SAVE_PATH = "dataset"
ENCODING_PATH = "model/encoding.pkl"

# Get roll number
roll_no = input("Enter your roll number: ").strip()
student_dir = os.path.join(SAVE_PATH, roll_no)
os.makedirs(student_dir, exist_ok=True)

# Queues for thread communication
frame_queue = queue.Queue()
encoding_list = []

# Encoding thread function
def encode_faces():
    while True:
        item = frame_queue.get()
        if item is None:
            break
        face_img, index = item
        rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_face)
        if encodings:
            encoding_list.append((roll_no, encodings[0]))
        frame_queue.task_done()

# Start encoder thread
encoder_thread = threading.Thread(target=encode_faces)
encoder_thread.start()

# Start webcam
cap = cv2.VideoCapture(0)
print("[INFO] Capturing frames. Please look at the camera...")

captured = 0

while captured < CAPTURE_COUNT:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to grab frame.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)

    if len(face_locations) == 1:
        y1, x2, y2, x1 = face_locations[0]
        face_img = frame[y1:y2, x1:x2]
        img_path = os.path.join(student_dir, f"{captured+1}.jpg")
        cv2.imwrite(img_path, face_img)

        # Put the face in the encoding queue
        frame_queue.put((face_img, captured+1))

        captured += 1
        print(f"[INFO] Captured {captured}/{CAPTURE_COUNT} images")

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{captured}/{CAPTURE_COUNT}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Capturing", frame)

    if cv2.waitKey(1) & 0xFF == ord('x'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
frame_queue.put(None)  # Signal thread to stop
encoder_thread.join()  # Wait for encoder to finish

# Save encodings
os.makedirs(os.path.dirname(ENCODING_PATH), exist_ok=True)
with open(ENCODING_PATH, 'wb') as f:
    pickle.dump(encoding_list, f)

print(f"[DONE] {captured} images saved to {student_dir}")
print(f"[ENCODED] {len(encoding_list)} face encodings saved to {ENCODING_PATH}")
