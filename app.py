from flask import Flask,render_template,request,jsonify,send_from_directory,current_app,url_for
import logging
logging.basicConfig(level=logging.DEBUG)
import os
from functions import process_bytes,process_uploaded_video,initialize
import threading
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

processing_status = None
files = None
@app.route('/')
def home():
    return render_template('home.html')

# Route for the live video page
@app.route("/live")
def live_video():
    return render_template("live.html")

# Route for the upload video page
@app.route("/upload")
def upload_video():
    return render_template("upload.html")


@socketio.on('send_frame')
def handle_frame(data):
    frame_data = data['frame']
    processed_frame = process_bytes(frame_data)
    socketio.emit('receive_frame', {'frame': f'data:image/jpeg;base64,{processed_frame}'})


@app.route('/process_video', methods=['POST'])
def process_video():
    global processing_status,files

    UPLOAD_FOLDER, PROCESSED_FOLDER = initialize()
    app = current_app
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

    file = request.files['video']
    if file:
        try:
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_path)
            files = file
            
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], 'processed_' + file.filename)
            
            processing_status = "processing"
            thread = threading.Thread(
                target=process_video_task,
                args=(input_path,output_path)
            )
            thread.start()
            return jsonify({'success': True})
        
        except Exception as e:
            print(f"Error during processing: {e}")
            return jsonify({'success': False, 'message': str(e)})

def process_video_task(input_path, output_path):
    global processing_status
    try:
        # Run the video processing
        process_uploaded_video(input_path,output_path)
        processing_status = 'completed'
    except Exception as e:
        processing_status = f'error: {str(e)}'

@app.route('/check_status', methods=['GET'])
def check_status():
    global processing_status,files
    if processing_status == 'completed':
        # If complete, provide the download URL
        file = files
        return jsonify({
            'status': 'completed',
            'download_url': url_for('download_file', filename='processed_' + file.filename)
        })
    return jsonify({'status': processing_status})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    app = current_app
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

portno = os.getenv("PORT")
# app.run(host='0.0.0.0',port=portno)
socketio.run(app, host='0.0.0.0', port=portno)

# socketio.run(app, host='0.0.0.0', port=5000)