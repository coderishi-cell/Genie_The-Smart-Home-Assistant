import cv2
import numpy as np
import face_recognition
from PIL import Image
import io
import requests
import base64

def debug_face_encoding_differences():
    """Debug exactly why live camera and static photos produce different face encodings"""
    
    api_base = "http://localhost:8000/api"
    
    print("🔬 Deep Debugging: Face Encoding Differences")
    print("=" * 60)
    
    # Step 1: Capture live camera frame (try Camera 0)
    print("\n1️⃣ Capturing Camera Frame...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Camera not available")
        return
    
    # Set high quality settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Could not capture frame")
        return
    
    print(f"✅ Captured frame: {frame.shape}")
    
    # Step 2: Process frame exactly like the live camera endpoint
    print("\n2️⃣ Processing Live Camera Frame...")
    
    # Apply same enhancements as live camera endpoint
    height, width = frame.shape[:2]
    if width > 800 or height > 600:
        scale = min(800/width, 600/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Apply sharpening
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    frame = cv2.filter2D(frame, -1, kernel)
    
    # Enhance contrast
    frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)
    
    # Encode like live camera
    encode_params = [
        cv2.IMWRITE_JPEG_QUALITY, 100,
        cv2.IMWRITE_JPEG_OPTIMIZE, 1,
    ]
    _, buffer = cv2.imencode('.jpg', frame, encode_params)
    live_image_bytes = buffer.tobytes()
    
    print(f"📏 Live camera image size: {len(live_image_bytes)} bytes")
    
    # Step 3: Load static photo for comparison
    print("\n3️⃣ Loading Static Photo...")
    static_photo_path = "backend/known_faces/Souvik Karmakar.jpg"
    
    try:
        with open(static_photo_path, 'rb') as f:
            static_image_bytes = f.read()
        print(f"📏 Static photo size: {len(static_image_bytes)} bytes")
    except Exception as e:
        print(f"❌ Could not load static photo: {e}")
        return
    
    # Step 4: Compare face encodings directly
    print("\n4️⃣ Direct Face Encoding Comparison...")
    
    def analyze_image_encoding(image_bytes, label):
        """Analyze face encoding for given image bytes"""
        print(f"\n🔍 Analyzing {label}:")
        
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_array = np.array(image)
        
        print(f"  📐 Image shape: {image_array.shape}")
        print(f"  💡 Brightness: {np.mean(image_array):.1f}")
        print(f"  📊 Data type: {image_array.dtype}")
        print(f"  🎯 Min/Max values: {image_array.min()}/{image_array.max()}")
        
        # Detect faces
        face_locations = face_recognition.face_locations(image_array, model="hog")
        print(f"  👤 Faces detected: {len(face_locations)}")
        
        if not face_locations:
            return None, None
        
        # Get face encodings with detailed analysis
        face_encodings = face_recognition.face_encodings(image_array, face_locations, num_jitters=1)
        
        if not face_encodings:
            print("  ❌ No face encodings generated")
            return None, None
        
        encoding = face_encodings[0]
        print(f"  🧬 Encoding shape: {encoding.shape}")
        print(f"  🔢 Encoding mean: {np.mean(encoding):.6f}")
        print(f"  📈 Encoding std: {np.std(encoding):.6f}")
        print(f"  ⬆️ Max value: {np.max(encoding):.6f}")
        print(f"  ⬇️ Min value: {np.min(encoding):.6f}")
        
        return encoding, face_locations[0]
    
    # Analyze both images
    live_encoding, live_location = analyze_image_encoding(live_image_bytes, "Live Camera")
    static_encoding, static_location = analyze_image_encoding(static_image_bytes, "Static Photo")
    
    # Step 5: Compare encodings
    if live_encoding is not None and static_encoding is not None:
        print("\n5️⃣ Encoding Comparison:")
        
        # Calculate face distance (lower = more similar)
        distance = face_recognition.face_distance([static_encoding], live_encoding)[0]
        print(f"  📏 Face distance: {distance:.6f}")
        
        # Calculate similarity score
        similarity = max(0.0, 1.0 - (distance / 0.6))
        print(f"  🎯 Similarity score: {similarity:.3f} ({similarity*100:.1f}%)")
        
        # Detailed difference analysis
        diff = np.abs(live_encoding - static_encoding)
        print(f"  🔄 Encoding difference (mean): {np.mean(diff):.6f}")
        print(f"  🔄 Encoding difference (max): {np.max(diff):.6f}")
        
        # Check if they would match with various thresholds
        thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]
        print(f"  🎚️ Match at thresholds:")
        for threshold in thresholds:
            match = similarity >= threshold
            print(f"    {threshold*100:2.0f}%: {'✅ YES' if match else '❌ NO'}")
    
    # Step 6: Test with backend API
    print("\n6️⃣ Backend API Test:")
    
    try:
        # Test live camera via API
        response = requests.post(f"{api_base}/doorbell/camera/capture-and-recognize")
        if response.status_code == 200:
            result = response.json()
            if result['faces_detected'] > 0:
                person = result['recognized_persons'][0]
                print(f"  🎥 Live API: {person['name']} - {person['confidence']*100:.1f}%")
            else:
                print("  🎥 Live API: No faces detected")
        else:
            print(f"  ❌ Live API failed: {response.status_code}")
        
        # Test static photo via API
        files = {'image': ('test.jpg', static_image_bytes, 'image/jpeg')}
        response = requests.post(f"{api_base}/face-recognition/recognize", files=files)
        if response.status_code == 200:
            result = response.json()
            if result['faces_detected'] > 0:
                person = result['recognized_persons'][0]
                print(f"  📷 Static API: {person['name']} - {person['confidence']*100:.1f}%")
            else:
                print("  📷 Static API: No faces detected")
        else:
            print(f"  ❌ Static API failed: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")
    if live_encoding is not None and static_encoding is not None:
        if similarity > 0.5:
            print("✅ Encodings are similar - issue might be in API processing")
        elif similarity > 0.3:
            print("⚠️ Encodings are somewhat similar - threshold/quality issue")
        else:
            print("❌ Encodings are very different - fundamental image processing issue")
    else:
        print("❌ Could not generate face encodings for comparison")

if __name__ == "__main__":
    debug_face_encoding_differences() 