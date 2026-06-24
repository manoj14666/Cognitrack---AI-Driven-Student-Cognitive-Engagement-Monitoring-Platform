#!/usr/bin/env python3
"""
Test script for Online Class Facial Emotion Detection Project
This script tests the basic functionality of the application.
"""

import sys
import os
import cv2
import numpy as np
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import tensorflow as tf
        print("✓ TensorFlow imported successfully")
    except ImportError as e:
        print(f"❌ TensorFlow import failed: {e}")
        return False
    
    try:
        import flask_socketio
        print("✓ Flask-SocketIO imported successfully")
    except ImportError as e:
        print(f"❌ Flask-SocketIO import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✓ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera functionality"""
    print("\n📹 Testing camera...")
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Camera not accessible")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read from camera")
            cap.release()
            return False
        
        print(f"✓ Camera working - Frame size: {frame.shape}")
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_emotion_detector():
    """Test emotion detection functionality"""
    print("\n🤖 Testing emotion detector...")
    
    try:
        from emotion_detector import EmotionDetector
        detector = EmotionDetector()
        print("✓ Emotion detector initialized")
        
        # Create a test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:] = (128, 128, 128)  # Gray image
        
        # Test detection (should handle no face gracefully)
        processed_frame, emotions = detector.detect_emotion(test_image)
        print("✓ Emotion detection function working")
        
        return True
        
    except Exception as e:
        print(f"❌ Emotion detector test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n🗄️ Testing database...")
    
    try:
        from database import db, User
        from app import app
        
        with app.app_context():
            # Test database connection
            users = User.query.all()
            print(f"✓ Database connection working - {len(users)} users found")
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application"""
    print("\n🌐 Testing Flask application...")
    
    try:
        from app import app
        
        # Test app creation
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✓ Flask application working")
                return True
            else:
                print(f"❌ Flask app returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_model_files():
    """Test if model files exist"""
    print("\n📁 Testing model files...")
    
    model_files = [
        "models/emotion_model.h5",
        "models/simple_emotion_model.h5"
    ]
    
    model_found = False
    for model_file in model_files:
        if os.path.exists(model_file):
            print(f"✓ Found model file: {model_file}")
            model_found = True
            break
    
    if not model_found:
        print("⚠️ No model files found - basic model will be created on first run")
    
    return True

def test_templates():
    """Test if template files exist"""
    print("\n📄 Testing template files...")
    
    template_files = [
        "templates/base.html",
        "templates/index.html",
        "templates/login.html",
        "templates/register.html",
        "templates/student.html",
        "templates/teacher.html"
    ]
    
    all_templates_exist = True
    for template_file in template_files:
        if os.path.exists(template_file):
            print(f"✓ Found template: {template_file}")
        else:
            print(f"❌ Missing template: {template_file}")
            all_templates_exist = False
    
    return all_templates_exist

def test_static_files():
    """Test if static files exist"""
    print("\n🎨 Testing static files...")
    
    static_files = [
        "static/css/style.css"
    ]
    
    all_static_exist = True
    for static_file in static_files:
        if os.path.exists(static_file):
            print(f"✓ Found static file: {static_file}")
        else:
            print(f"❌ Missing static file: {static_file}")
            all_static_exist = False
    
    return all_static_exist

def run_all_tests():
    """Run all tests"""
    print("🧪 Online Class Facial Emotion Detection - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Camera Test", test_camera),
        ("Emotion Detector Test", test_emotion_detector),
        ("Database Test", test_database),
        ("Flask App Test", test_flask_app),
        ("Model Files Test", test_model_files),
        ("Template Files Test", test_templates),
        ("Static Files Test", test_static_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application, run:")
        print("python app.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("You may still be able to run the application with limited functionality.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
