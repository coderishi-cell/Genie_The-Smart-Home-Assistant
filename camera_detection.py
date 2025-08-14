import cv2
import numpy as np

def detect_cameras():
    """Detect all available cameras and their capabilities"""
    print("🎥 Detecting Available Cameras...")
    
    available_cameras = []
    
    # Test camera indices 0-5 (usually enough for most systems)
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Test if we can actually read a frame
            ret, frame = cap.read()
            if ret and frame is not None:
                available_cameras.append({
                    'index': i,
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'frame_quality': frame.shape if len(frame.shape) == 3 else None
                })
                print(f"✅ Camera {i}: {width}x{height} @ {fps:.1f}fps")
            else:
                print(f"❌ Camera {i}: Cannot read frames")
            
            cap.release()
        else:
            print(f"❌ Camera {i}: Not available")
    
    return available_cameras

def test_camera_quality(camera_index):
    """Test camera quality for face recognition"""
    print(f"\n🔍 Testing Camera {camera_index} Quality...")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_index}")
        return False
    
    # Set optimal settings for face recognition
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Test frame capture
    ret, frame = cap.read()
    if not ret:
        print("❌ Cannot capture frame")
        cap.release()
        return False
    
    # Analyze frame quality
    height, width = frame.shape[:2]
    print(f"📐 Actual resolution: {width}x{height}")
    
    # Check brightness
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    print(f"💡 Brightness level: {brightness:.1f}/255")
    
    # Check sharpness (Laplacian variance)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = laplacian.var()
    print(f"🔎 Sharpness score: {sharpness:.1f}")
    
    # Test face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    print(f"👤 Faces detected: {len(faces)}")
    
    cap.release()
    
    # Quality assessment
    quality_score = 0
    if width >= 640 and height >= 480:
        quality_score += 25
    if brightness > 50 and brightness < 200:
        quality_score += 25
    if sharpness > 100:
        quality_score += 25
    if len(faces) > 0:
        quality_score += 25
    
    print(f"🏆 Overall quality score: {quality_score}/100")
    return quality_score >= 75

if __name__ == "__main__":
    print("🎯 Camera Detection and Quality Test")
    print("=" * 40)
    
    # Detect all cameras
    cameras = detect_cameras()
    
    if not cameras:
        print("\n❌ No cameras detected!")
        exit(1)
    
    print(f"\n📋 Found {len(cameras)} camera(s)")
    
    # Test each camera quality
    best_camera = None
    best_score = 0
    
    for camera in cameras:
        print(f"\n{'='*20} Camera {camera['index']} {'='*20}")
        if test_camera_quality(camera['index']):
            print(f"✅ Camera {camera['index']} is suitable for face recognition")
            if best_camera is None:
                best_camera = camera['index']
        else:
            print(f"⚠️ Camera {camera['index']} may have quality issues")
    
    if best_camera is not None:
        print(f"\n🎯 Recommended camera: Index {best_camera}")
        print("Use this camera index in your face recognition system.")
    else:
        print(f"\n⚠️ No cameras meet optimal quality standards.")
        print("Try improving lighting or camera positioning.") 