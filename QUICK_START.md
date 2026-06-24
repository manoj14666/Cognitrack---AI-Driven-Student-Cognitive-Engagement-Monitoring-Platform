# Quick Start Guide - Teacher Dashboard Student Online Status

## ✅ Issue Fixed
- Teacher dashboard now shows students as "Online" when they're actively using the student interface
- Added all missing API endpoints for attention monitoring

## 🚀 How to Use the Application

### 1. Start the Server
```bash
python annu.py
```

### 2. Access the Application
- **Student Interface**: http://127.0.0.1:5000/student
- **Teacher Dashboard**: http://127.0.0.1:5000/teacher
- **Default Login**: username='teacher', password='password'

### 3. Test the Online Status Feature

#### For Students:
1. Open http://127.0.0.1:5000/student in one browser window
2. Login as a student (create an account if needed)
3. Click "Start Detection" button
4. Allow camera access when prompted
5. The student is now "online"

#### For Teachers:
1. Open http://127.0.0.1:5000/teacher in another browser window (or tab)
2. Login as teacher (username: teacher, password: password)
3. You should see the student appear as "Online" in the dashboard
4. Real-time emotion updates will appear in the "Real-time Attention Monitoring" panel

### 4. Send Feedback to Students

**Option 1: Via Student Card**
1. In the Teacher Dashboard, find the student in the "Active Students" list
2. Click the "Send Feedback" button next to the student
3. Fill in the message and send

**Option 2: Via Feedback Form**
1. In the Teacher Dashboard right sidebar, use the "Send Feedback" form
2. Select the student from dropdown
3. Choose feedback type (General, Encouragement, Warning)
4. Write your message
5. Click "Send Feedback" button

### 5. Monitor Student Attention

The teacher dashboard now shows:
- **Current Emotion**: Detected emotion in real-time
- **Attention Score**: 0-100% attentiveness score
- **Attention Status**: 
  - Attentive (80-100%)
  - Partially Attentive (50-79%)
  - Distracted (20-49%)
  - Inattentive (0-19%)
  - Absent / Disengaged
- **Face Detection Status**: Whether student's face is detected

### 6. View Attention Alerts

The attention alerts panel shows:
- Low attention scores (<30%)
- Face absence for extended periods
- Distracted or inattentive status
- Click the checkmark to acknowledge alerts

## 🔧 Features Included

### Eye Tracking & Attention Monitoring
- ✅ Real-time head pose estimation (pitch, yaw, roll)
- ✅ Eye gaze direction tracking (left/center/right)
- ✅ Blink detection
- ✅ Eye openness monitoring (left/right eyes)
- ✅ Face quality assessment
- ✅ Face presence monitoring
- ✅ Attention score calculation (0-100%)
- ✅ Real-time WebSocket updates

### Teacher Dashboard
- ✅ Student online/offline status
- ✅ Real-time emotion monitoring
- ✅ Attention monitoring
- ✅ Feedback sending system
- ✅ Attention alert system
- ✅ Student statistics

### Student Interface
- ✅ Camera initialization
- ✅ Real-time emotion detection
- ✅ Attention score display
- ✅ Teacher feedback reception
- ✅ Session statistics

## 📊 What You'll See

**Teacher Dashboard shows:**
- Student Name
- Online/Offline Status
- Current Emotion
- Attention Score (%)
- Attention Status
- Face Detected Status
- Timestamp

**Student Interface shows:**
- Live camera feed
- Current emotion
- Engagement score (0-100%)
- Attention score (0-100%)
- Attention status
- Recent emotions history
- Teacher feedback messages

## 🎯 Testing Instructions

1. **Start the server**: `python annu.py`
2. **Open Student Interface** in Browser 1: http://127.0.0.1:5000/student
3. **Login and start detection**
4. **Open Teacher Dashboard** in Browser 2: http://127.0.0.1:5000/teacher
5. **You should see**:
   - Student appears as "Online"
   - Real-time emotion updates
   - Attention score and status
   - Send feedback button is clickable

## 🐛 Troubleshooting

**Student shows as "Offline":**
- Make sure student clicked "Start Detection"
- Check that camera is working
- Refresh both pages

**No emotion detection:**
- Ensure good lighting
- Face should be clearly visible
- Check camera permissions

**404 errors for /api/attention_alerts:**
- Restart the server to load new routes
- Check terminal for any errors

## 📝 Notes

- The server automatically creates the database tables on first run
- Default teacher account is created automatically
- Student accounts need to be created via registration
- All data is stored locally in SQLite database

