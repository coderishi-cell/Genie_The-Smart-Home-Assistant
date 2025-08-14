import requests
import cv2
import base64
import numpy as np
from io import BytesIO
from PIL import Image
import face_recognition

def test_live_vs_static_recognition():
    """Compare live camera processing vs static photo processing"""
    
    api_base = "http://localhost:8000/api"
    
    print("🔍 Debugging Live Camera vs Static Photo Recognition...")
    
    # Test 1: Verify backend is running
    print("\n1️⃣ Checking backend status...")
    try:
        response = requests.get(f"{api_base}/face-recognition/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Backend running - Known persons: {status.get('known_persons_count', 0)}")
            print(f"📋 Known persons: {status.get('known_persons', [])}")
        else:
            print(f"❌ Backend not responding: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return
    
    # Test 2: Static photo test (should work)
    print("\n2️⃣ Testing static photo recognition...")
    try:
        with open("souvik_photo.jpg", "rb") as f:
            files = {"file": ("souvik_photo.jpg", f, "image/jpeg")}
            response = requests.post(f"{api_base}/face-recognition/upload-test", files=files)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Static photo test: {result}")
        else:
            print(f"❌ Static photo test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Static photo test error: {e}")
    
    # Test 3: Capture live camera frame and test
    print("\n3️⃣ Testing live camera frame capture...")
    cap = cv2.VideoCapture(1)  # Use USB camera for better quality
    
    if not cap.isOpened():
        print("❌ Cannot access camera")
        return
    
    print("📷 Camera opened, capturing frame...")
    ret, frame = cap.read()
    
    if not ret:
        print("❌ Failed to capture frame")
        cap.release()
        return
    
    print(f"📸 Frame captured: {frame.shape}")
    
    # Test 4: Test different image processing methods
    print("\n4️⃣ Testing different image processing methods...")
    
    # Method 1: Direct frame encoding (like live camera)
    _, buffer1 = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    image_bytes1 = buffer1.tobytes()
    
    # Method 2: RGB conversion then back to BGR (like some face recognition)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
    _, buffer2 = cv2.imencode('.jpg', bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    image_bytes2 = buffer2.tobytes()
    
    # Method 3: PIL conversion (like static photos)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    buffer3 = BytesIO()
    pil_image.save(buffer3, format='JPEG', quality=95)
    image_bytes3 = buffer3.getvalue()
    
    # Test each method
    methods = [
        ("Direct CV2 encoding", image_bytes1),
        ("BGR->RGB->BGR encoding", image_bytes2), 
        ("PIL encoding", image_bytes3)
    ]
    
    for method_name, image_bytes in methods:
        try:
            print(f"\n🧪 Testing {method_name}...")
            
            # Send to live camera endpoint
            files = {"image": ("frame.jpg", BytesIO(image_bytes), "image/jpeg")}
            response = requests.post(f"{api_base}/doorbell/camera/capture-and-recognize", files=files)
            
            if response.status_code == 200:
                result = response.json()
                faces = result.get("faces", [])
                print(f"   📊 Detected {len(faces)} faces")
                
                for i, face in enumerate(faces):
                    name = face.get("name", "Unknown")
                    confidence = face.get("confidence", 0.0)
                    print(f"   👤 Face {i+1}: {name} ({confidence:.1f}%)")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 5: Direct face_recognition library test
    print("\n5️⃣ Testing face_recognition library directly...")
    try:
        # Convert frame to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face encodings
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        print(f"   📍 Found {len(face_locations)} faces")
        print(f"   🧬 Generated {len(face_encodings)} encodings")
        
        if len(face_encodings) > 0:
            encoding = face_encodings[0]
            print(f"   📏 Encoding shape: {encoding.shape}")
            print(f"   📈 Encoding sample: {encoding[:5]}")
        
    except Exception as e:
        print(f"   ❌ Direct face_recognition error: {e}")
    
    cap.release()
    print("\n🔍 Debug test completed!")

if __name__ == "__main__":
    test_live_vs_static_recognition() 