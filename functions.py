import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as im
import base64
import os

model_best = load_model('face_model.h5')
class_names = ['Angry', 'Disgusted', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def process_bytes(frame_data):
    header, encoded = frame_data.split(',', 1)
    decoded = base64.b64decode(encoded)
    np_data = np.frombuffer(decoded, dtype=np.uint8)
    frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

    frame = process_frame(frame)
    
    _, buffer = cv2.imencode('.jpg', frame)
    processed_frame = base64.b64encode(buffer).decode('utf-8')
    return processed_frame

# this is for normal function without socket io 
# def process_bytes(data):
#     nparr = np.frombuffer(data, np.uint8)
#     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
#     frame = process_frame(frame)
    
#     success, buffer = cv2.imencode('.jpg', frame)
#     if not success:
#         raise ValueError("Failed to encode image")
#     processed_frame = base64.b64encode(buffer).decode('utf-8')
#     return processed_frame

def process_frame(frame):
    if frame is None:
        # frame = np.zeros((640, 480, 3), dtype=np.uint8)
        return frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
    for (x, y, w, h) in faces:
        face_roi = frame[y:y + h, x:x + w]
        face_image = cv2.resize(face_roi, (48, 48))
        face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        face_image = im.img_to_array(face_image)
        face_image = np.expand_dims(face_image, axis=0)
        face_image = np.vstack([face_image])

        predictions = model_best.predict(face_image)
        emotion_label = class_names[np.argmax(predictions)]

        cv2.putText(frame, emotion_label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2)

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return frame

def process_uploaded_video(input_path,output_path):
    cap = cv2.VideoCapture(input_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))

    processed_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # processed_frame = detection(frame)
        processed_frame = process_frame(frame)
        processed_frames.append(processed_frame)
    cap.release()
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))
    for frame in processed_frames:
        out.write(frame)
    out.release()
    return output_path

def create_directories():
    UPLOAD_FOLDER = 'uploads' 
    PROCESSED_FOLDER = 'processed'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    return UPLOAD_FOLDER, PROCESSED_FOLDER

def initialize():
    UPLOAD_FOLDER, PROCESSED_FOLDER = create_directories()
    return UPLOAD_FOLDER, PROCESSED_FOLDER

