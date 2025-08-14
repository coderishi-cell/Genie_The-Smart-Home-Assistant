import requests
import cv2
import base64
import numpy as np

def test_live_camera_recognition():
    """Test the live camera recognition endpoint specifically"""
    
    api_base = "http://localhost:8000/api"
    
    print("🔍 Testing Live Camera Recognition...")
    
    # Test 1: Check if backend is running with updated face data
    print("\n1️⃣ Checking backend status...")
    try:
        response = requests.get(f"{api_base}/face-recognition/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Backend running - Known persons: {status.get('known_persons_count')}")
        else:
            print(f"❌ Backend not responding: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        return
    
    # Test 2: Try the live camera capture endpoint directly
    print("\n2️⃣ Testing live camera capture endpoint...")
    try:
        response = requests.post(f"{api_base}/doorbell/camera/capture-and-recognize")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Live camera capture successful!")
            print(f"📊 Response: {result}")
            
            if result.get('success'):
                faces = result.get('faces_detected', 0)
                persons = result.get('recognized_persons', [])
                
                print(f"🔍 Faces detected: {faces}")
                
                if persons:
                    for person in persons:
                        name = person.get('name', 'Unknown')
                        confidence = person.get('confidence', 0) * 100
                        print(f"👤 {name}: {confidence:.1f}% confidence")
                else:
                    print("❌ No persons recognized")
            else:
                print(f"❌ Camera capture failed: {result.get('error')}")
        else:
            print(f"❌ Live camera request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing live camera: {e}")
    
    # Test 3: Simulate live camera with a known photo
    print("\n3️⃣ Testing recognition with known photo via live API...")
    try:
        # Read the same photo we used successfully before
        photo_path = "backend/known_faces/Souvik Karmakar.jpg"
        
        with open(photo_path, 'rb') as f:
            photo_data = f.read()
        
        # Use the main recognition endpoint (not live camera)
        files = {'image': ('test.jpg', photo_data, 'image/jpeg')}
        data = {'doorbell_mode': 'true'}
        
        response = requests.post(f"{api_base}/face-recognition/recognize", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                persons = result.get('recognized_persons', [])
                if persons:
                    for person in persons:
                        name = person.get('name')
                        confidence = person.get('confidence', 0) * 100
                        print(f"✅ Static photo recognition: {name} - {confidence:.1f}%")
                else:
                    print("❌ Static photo not recognized")
            else:
                print(f"❌ Static photo recognition failed: {result.get('error')}")
        else:
            print(f"❌ Static photo request failed: {response.status_code}")
            
    except FileNotFoundError:
        print("❌ Test photo not found")
    except Exception as e:
        print(f"❌ Error testing static photo: {e}")
    
    # Test 4: Check if there's a difference in face engine status
    print("\n4️⃣ Detailed face engine check...")
    try:
        response = requests.get(f"{api_base}/face-recognition/persons")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                persons = data.get('persons', [])
                print(f"📋 Known persons in system:")
                for person in persons:
                    print(f"  • {person.get('name')} - Access: {person.get('access_level')}")
            else:
                print("❌ Could not get persons list")
        else:
            print(f"❌ Persons request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting persons: {e}")

if __name__ == "__main__":
    test_live_camera_recognition() 