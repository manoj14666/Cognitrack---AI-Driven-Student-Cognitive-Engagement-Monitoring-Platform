from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import base64
import cv2
import numpy as np
from datetime import datetime
import json

from database import db, User, Session, EmotionData, Feedback, ClassRoom, AttentionAlert
from emotion_detector import EmotionDetector
from auth_verifier import AuthVerifier

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emotion_detection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize emotion detector and auth verifier
emotion_detector = EmotionDetector()
auth_verifier = AuthVerifier()

# Global dict to rate-limit verification
session_verification_timers = {}
last_audio_alert_timers = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_interface'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_interface'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = 'student'  # Force role to student, no more teacher registration
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
        
        face_encoding_json = None
        if role == 'student':
            face_image_data = request.form.get('face_image')
            if face_image_data and face_image_data != '[]':
                try:
                    images_b64 = json.loads(face_image_data)
                    cv2_images = []
                    for b64 in images_b64:
                        img_bytes = base64.b64decode(b64.split(',')[1])
                        nparr = np.frombuffer(img_bytes, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        cv2_images.append(img)
                    
                    avg_embedding = auth_verifier.compute_average_embedding(cv2_images)
                    if avg_embedding:
                        face_encoding_json = json.dumps(avg_embedding)
                except Exception as e:
                    print(f"Error processing registration images: {e}")

        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            face_encoding=face_encoding_json
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/student')
@login_required
def student_interface():
    if current_user.role != 'student':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Get active session or create new one
    active_session = Session.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not active_session:
        active_session = Session(
            user_id=current_user.id,
            session_name=f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        db.session.add(active_session)
        db.session.commit()
    
    return render_template('student.html', session_id=active_session.id)

@app.route('/teacher')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Get all students
    students = User.query.filter_by(role='student').all()
    total_students = len(students)
    
    # Get recent sessions
    recent_sessions = Session.query.filter_by(is_active=True).all()
    
    return render_template('teacher.html', students=students, sessions=recent_sessions, total_students=total_students)

@app.route('/api/audio_data', methods=['POST'])
@login_required
def process_audio_data():
    if current_user.role != 'student':
        return jsonify({'success': False, 'error': 'Only students can send audio data'})
        
    try:
        data = request.json
        audio_data_b64 = data.get('audio_data')
        
        if audio_data_b64:
            # Decode base64 to bytes
            audio_bytes = base64.b64decode(audio_data_b64)
            # Convert bytes to int16 array
            int16_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            if len(int16_array) > 0:
                float_array = int16_array.astype(np.float32)
                rms = np.sqrt(np.mean(float_array**2))
                noise_level = (rms / 32768.0) * 100.0 * 5  # Scaled for visibility
                
                if noise_level > 25.0:  # Threshold for too much noise
                    current_time = datetime.now().timestamp()
                    last_alert = last_audio_alert_timers.get(current_user.id, 0)
                    
                    if current_time - last_alert > 10.0:  # 10s cooldown
                        last_audio_alert_timers[current_user.id] = current_time
                        socketio.emit('audio_alert', {
                            'student_id': current_user.id,
                            'student_name': current_user.username,
                            'message': f"From {current_user.username} too much noises are coming",
                            'noise_level': round(noise_level, 2),
                            'timestamp': datetime.now().isoformat()
                        }, room='teacher_room')
                
                return jsonify({'success': True, 'noise_level': noise_level})
                
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/emotion_data', methods=['POST'])
@login_required
def process_emotion_data():
    if current_user.role != 'student':
        return jsonify({'success': False, 'error': 'Only students can send emotion data'})
        
    try:
        data = request.json
        image_data = data['image']
        session_id = data['session_id']
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect emotions
        processed_frame, emotions_data = emotion_detector.detect_emotion(frame)
        
        # Calculate engagement score
        engagement_score = emotion_detector.get_engagement_score(emotions_data)
        
        # Identity Verification Logic (throttled to every 2 seconds)
        current_time = datetime.now().timestamp()
        last_verify_time = session_verification_timers.get(session_id, 0)
        session = Session.query.get(session_id)
        attendance_status = session.attendance_status if session else "Present"
        
        if current_time - last_verify_time > 2.0:
            stored_embedding_str = current_user.face_encoding
            stored_embedding = json.loads(stored_embedding_str) if stored_embedding_str else None
            
            # verify identity
            status, dist = auth_verifier.verify_identity(frame, stored_embedding)
            session_verification_timers[session_id] = current_time
            
            previous_status = attendance_status
            attendance_status = status
            
            if session:
                session.attendance_status = attendance_status
                
            if previous_status != status:
                socketio.emit('attendance_update', {
                    'student_id': current_user.id,
                    'student_name': current_user.username,
                    'status': 'Present' if status == 'Present' else ('Intruder' if status == 'Imposter Detected' else 'Absent'),
                    'message': f"Face Verification: {status}",
                    'timestamp': datetime.now().isoformat()
                }, room='teacher_room')
        
        # Calculate Attention Metrics
        attention_score = engagement_score * 100.0 if attendance_status != "No Face Detected" else 0.0
        attention_status = "Attentive" if attention_score >= 70 else ("Partially Attentive" if attention_score >= 40 else "Inattentive")

        # Save emotion data to database
        for emotion_data in emotions_data:
            emotion_record = EmotionData(
                session_id=session_id,
                emotion=emotion_data['emotion'],
                confidence=emotion_data['confidence'],
                engagement_score=engagement_score,
                face_detected=(attendance_status != "No Face Detected"),
                intruder_detected=(attendance_status == "Imposter Detected"),
                attention_score=attention_score,
                attention_status=attention_status
            )
            db.session.add(emotion_record)
            
        # Alert Generation Logic
        if attention_score < 40 or attendance_status == "No Face Detected":
            last_alert = AttentionAlert.query.filter_by(session_id=session_id).order_by(AttentionAlert.timestamp.desc()).first()
            if not last_alert or (datetime.utcnow() - last_alert.timestamp).total_seconds() > 60:
                alert_type = 'low_attention' if attendance_status != "No Face Detected" else 'face_absent'
                alert_message = f"{current_user.username} is currently {attention_status.lower()}"
                
                alert = AttentionAlert(
                    session_id=session_id,
                    student_id=current_user.id,
                    alert_type=alert_type,
                    alert_message=alert_message,
                    attention_score=attention_score
                )
                db.session.add(alert)
                db.session.commit()
                
                socketio.emit('student_attention_alert', {
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'attention_status': attention_status,
                    'attention_score': attention_score,
                    'alert_type': alert_type
                }, room='teacher_room')
        
        db.session.commit()
        
        # Emit to teacher dashboard
        socketio.emit('emotion_update', {
            'user_id': current_user.id,
            'username': current_user.username,
            'emotions': emotions_data,
            'engagement_score': engagement_score,
            'attendance_status': attendance_status,
            'attention_score': attention_score,
            'attention_status': attention_status,
            'face_detected': (attendance_status != "No Face Detected"),
            'person_count': len(emotions_data),
            'intruder_detected': (attendance_status == "Imposter Detected"),
            'timestamp': datetime.now().isoformat()
        }, room='teacher_room')
        
        return jsonify({
            'success': True,
            'emotions': emotions_data,
            'engagement_score': engagement_score,
            'attendance_status': attendance_status,
            'attention_score': attention_score,
            'attention_status': attention_status,
            'face_detected': (attendance_status != "No Face Detected"),
            'person_count': len(emotions_data),
            'intruder_detected': (attendance_status == "Imposter Detected")
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error processing emotion data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/attention_alerts', methods=['GET'])
@login_required
def get_attention_alerts():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'})
        
    try:
        # Get active sessions alerts
        alerts = AttentionAlert.query.filter_by(is_acknowledged=False).order_by(AttentionAlert.timestamp.desc()).all()
        
        return jsonify([{
            'id': alert.id,
            'student_id': alert.student_id,
            'student_name': alert.student.username,
            'alert_type': alert.alert_type,
            'alert_message': alert.alert_message,
            'attention_score': alert.attention_score,
            'timestamp': alert.timestamp.isoformat()
        } for alert in alerts])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send_feedback', methods=['POST'])
@login_required
def send_feedback():
    if current_user.role != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        data = request.json
        student_id = data['student_id']
        message = data['message']
        feedback_type = data.get('feedback_type', 'general')
        session_id = data.get('session_id')
        
        if not session_id:
            active_session = Session.query.filter_by(user_id=student_id, is_active=True).first()
            if active_session:
                session_id = active_session.id
            else:
                return jsonify({'success': False, 'error': 'Student has no active session to receive messages'})
        
        feedback = Feedback(
            teacher_id=current_user.id,
            student_id=student_id,
            session_id=session_id,
            message=message,
            feedback_type=feedback_type
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        # Emit to student
        socketio.emit('feedback_received', {
            'message': message,
            'feedback_type': feedback_type,
            'teacher': current_user.username,
            'timestamp': datetime.now().isoformat()
        }, room=f'student_{student_id}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/student_stats/<int:student_id>')
@login_required
def get_student_stats(student_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'})
    
    # Get emotion data for the student's recent sessions
    sessions = Session.query.filter_by(user_id=student_id).order_by(Session.start_time.desc()).limit(5).all()
    
    stats = []
    for session in sessions:
        emotion_data = EmotionData.query.filter_by(session_id=session.id).all()
        
        if emotion_data:
            emotions = [data.emotion for data in emotion_data]
            avg_engagement = sum(data.engagement_score for data in emotion_data) / len(emotion_data)
            
            stats.append({
                'session_id': session.id,
                'session_name': session.session_name,
                'start_time': session.start_time.isoformat(),
                'emotions': emotions,
                'avg_engagement': avg_engagement,
                'total_records': len(emotion_data)
            })
    
    return jsonify(stats)

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            join_room('teacher_room')
        else:
            join_room(f'student_{current_user.id}')
            socketio.emit('student_presence', {
                'user_id': current_user.id,
                'status': 'online',
                'username': current_user.username
            }, room='teacher_room')
        print(f"User {current_user.username} connected")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            leave_room('teacher_room')
        else:
            leave_room(f'student_{current_user.id}')
            socketio.emit('student_presence', {
                'user_id': current_user.id,
                'status': 'offline',
                'username': current_user.username
            }, room='teacher_room')
        print(f"User {current_user.username} disconnected")

with app.app_context():
    db.create_all()
    
    # Create default teacher account if none exists
    if not User.query.filter_by(role='teacher').first():
        teacher = User(
            username='teacher',
            email='teacher@example.com',
            password_hash=generate_password_hash('password'),
            role='teacher'
        )
        db.session.add(teacher)
        db.session.commit()
        print("Default teacher account created: username='teacher', password='password'")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
