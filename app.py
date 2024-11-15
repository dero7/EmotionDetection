from flask import Flask,render_template,request,jsonify
from flask_socketio import SocketIO
import cv2
import base64
import numpy as np
from deepface import DeepFace
import logging
logging.basicConfig(level=logging.DEBUG)
import os

app = Flask(__name__)
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def process_video(data):
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    predictions = DeepFace.analyze(frame ,actions=['emotion'],enforce_detection=False)
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray,1.1,4)

    res = [ sub['dominant_emotion'] for sub in predictions ]
    name = res[0]
    font = cv2.FONT_HERSHEY_SIMPLEX
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.putText(frame,name,(x+2,y-10),font,1,(0,0,255),2)

    success, buffer = cv2.imencode('.jpg', frame)
    if not success:
        raise ValueError("Failed to encode image")
    processed_frame = base64.b64encode(buffer).decode('utf-8')
    return processed_frame

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_frame', methods=['POST'])
def process_frame():
    try:
        data = request.json
        frame_data = data.get('frame')
        if not frame_data:
            return jsonify({'message': 'No frame data provided'}), 400
        if not frame_data.startswith('data:image/jpeg;base64,'):
            return jsonify({'message': 'Frame data is not properly Base64 encoded'}), 400
        frame_data = frame_data[len('data:image/jpeg;base64,'):]
        if not frame_data:
            return jsonify({'message': 'Frame data is empty after base64 split'}), 400
        try:
            image_bytes = base64.b64decode(frame_data)
        except (base64.binascii.Error, ValueError) as e:
            return jsonify({'message': 'Failed to decode Base64 frame data'}), 400
        if len(image_bytes) < 1000:
            logging.error('Decoded image data is too short')
            return jsonify({'message': 'Decoded image data is too short'}), 400
        processed_frame_base64 = process_video(image_bytes)
        
        if not processed_frame_base64:       
            return jsonify({'message': 'Error processing frame'}), 500
        return jsonify({'processed_frame': f"data:image/jpeg;base64,{processed_frame_base64}"})
    
    except Exception as e:
        logging.error(f"Unexpected error in /process_frame route: {e}")
        return jsonify({'message': 'Unexpected error occurred during frame processing'}), 500


portno = os.environ.get('PORT')
app.run(host='0.0.0.0', port=portno,debug=True)