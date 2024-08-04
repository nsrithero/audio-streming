from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav'}
socketio = SocketIO(app)

current_song = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

@app.route('/delete_audio', methods=['POST'])
def delete_audio():
    filename = request.form['filename']
    delete_file(filename)
    return jsonify({'message': 'File deleted successfully'})

@app.route('/delete_all_audio', methods=['POST'])
def delete_all_audio():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    for file in files:
        delete_file(file)
    return jsonify({'message': 'All audio files deleted successfully'})

@socketio.on('play_audio')
def handle_play_audio(data):
    global current_song
    current_song = data['filename']
    audio_url = url_for('stream_audio', filename=current_song, _external=True)
    socketio.emit('play_audio', {'audio_url': audio_url})

@socketio.on('stop_audio')
def handle_stop_audio():
    socketio.emit('stop_audio')

@socketio.on('start_audio')
def handle_start_audio():
    socketio.emit('start_audio')

@socketio.on('connect')
def handle_connect():
    global current_song
    if current_song:
        audio_url = url_for('stream_audio', filename=current_song, _external=True)
    else:
        audio_files = os.listdir(app.config['UPLOAD_FOLDER'])
        if audio_files:
            current_song = audio_files[0]
            audio_url = url_for('stream_audio', filename=current_song, _external=True)
        else:
            audio_url = None
    if audio_url:
        socketio.emit('play_audio', {'audio_url': audio_url})

@app.route('/')
def index():
    audio_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', audio_files=audio_files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            socketio.emit('play_audio', {'filename': filename})
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/upload_page')
def upload_page():
    return render_template('upload.html')

@app.route('/audio/<filename>')
def stream_audio(filename):
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(audio_path)

@app.route('/get_audio_list')
def get_audio_list():
    audio_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({'audio_files': audio_files})

