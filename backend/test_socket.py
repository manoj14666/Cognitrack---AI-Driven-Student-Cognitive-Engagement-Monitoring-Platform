import requests
import socketio
import time

# Create student
s_session = requests.Session()
s_session.post('http://localhost:5000/register', data={'username': 'test_student', 'email': 'test@test.com', 'password': 'password', 'role': 'student'})
s_session.post('http://localhost:5000/login', data={'username': 'test_student', 'password': 'password'})

# Create teacher
t_session = requests.Session()
t_session.post('http://localhost:5000/login', data={'username': 'teacher', 'password': 'password'})

t_sio = socketio.Client(request_timeout=5)
s_sio = socketio.Client(request_timeout=5)

@t_sio.on('student_presence')
def on_presence(data):
    print("TEACHER RECEIVED PRESENCE:", data)

@t_sio.on('emotion_update')
def on_emotion(data):
    print("TEACHER RECEIVED EMOTION:", data)

print("Connecting teacher...")
t_sio.connect('http://localhost:5000', headers={'Cookie': '; '.join([f"{k}={v}" for k,v in t_session.cookies.items()])})
time.sleep(1)

print("Connecting student...")
s_sio.connect('http://localhost:5000', headers={'Cookie': '; '.join([f"{k}={v}" for k,v in s_session.cookies.items()])})
time.sleep(2)

print("Student creating a session and sending emotion data via API")
s_session.get('http://localhost:5000/student') # creates session
res = s_session.post('http://localhost:5000/api/emotion_data', json={
    'image': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/AL+A/9k=',
    'session_id': 1
})
print("API Response:", res.json())
time.sleep(2)
t_sio.disconnect()
s_sio.disconnect()
