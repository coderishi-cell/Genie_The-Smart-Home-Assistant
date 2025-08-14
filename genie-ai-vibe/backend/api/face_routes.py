from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict, List
import io
import json
import logging
from pydantic import BaseModel
import cv2
import asyncio
import base64
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from core.face_engine import FaceRecognitionEngine
from core.device_simulator import DeviceSimulator

logger = logging.getLogger(__name__)

# Initialize face recognition engine
face_engine = FaceRecognitionEngine()

# Initialize device simulator for door control
device_sim = DeviceSimulator()

router = APIRouter()

# Pydantic models
class PersonMetadata(BaseModel):
    access_level: str = "standard"  # standard, admin, guest
    notes: str = ""

class RecognitionResult(BaseModel):
    success: bool
    faces_detected: int
    recognized_persons: List[Dict]
    timestamp: Optional[str] = None
    error: Optional[str] = None

@router.post("/face-recognition/add-person")
async def add_known_person(
    name: str = Form(...),
    photo: UploadFile = File(...),
    access_level: str = Form("standard"),
    notes: str = Form("")
):
    """Add a new known person to the face recognition database"""
    try:
        if not photo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        photo_data = await photo.read()
        
        metadata = {
            "access_level": access_level,
            "notes": notes
        }
        
        result = face_engine.add_known_person(name, photo_data, metadata)
        
        if result["success"]:
            logger.info(f"Successfully added person: {name}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"],
                    "person_count": result["person_count"],
                    "data": {
                        "name": name,
                        "access_level": access_level,
                        "notes": notes,
                        "face_locations": result.get("face_locations", 0)
                    }
                }
            )
        else:
            logger.error(f"Failed to add person {name}: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Failed to add person")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error adding person {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/face-recognition/recognize")
async def recognize_faces(
    image: UploadFile = File(...),
    doorbell_mode: bool = Form(False)
):
    """Recognize faces in the provided image"""
    try:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_data = await image.read()
        result = face_engine.recognize_face(image_data)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Recognition failed"))
        
        # Handle doorbell mode
        doorbell_response = None
        if doorbell_mode and result["recognized_persons"]:
            doorbell_response = await handle_doorbell_recognition(result["recognized_persons"])
        
        response_data = {
            "success": result["success"],
            "faces_detected": result["faces_detected"],
            "recognized_persons": result["recognized_persons"],
            "timestamp": result.get("timestamp"),
            "doorbell_response": doorbell_response
        }
        
        logger.info(f"Face recognition completed: {result['faces_detected']} faces detected")
        return JSONResponse(status_code=200, content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in face recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/face-recognition/persons")
async def list_known_persons():
    """List all known persons in the face recognition database"""
    try:
        result = face_engine.list_known_persons()
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "total_persons": result["total_persons"],
                    "persons": result["persons"]
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to list persons"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing known persons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/face-recognition/persons/{person_name}")
async def remove_known_person(person_name: str):
    """Remove a person from the face recognition database"""
    try:
        result = face_engine.remove_known_person(person_name)
        
        if result["success"]:
            logger.info(f"Successfully removed person: {person_name}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"],
                    "remaining_persons": result["remaining_persons"]
                }
            )
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Person not found"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing person {person_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/face-recognition/persons/{person_name}/photo")
async def get_person_photo(person_name: str):
    """Get the photo of a known person"""
    try:
        photo_data = face_engine.get_person_photo(person_name)
        
        if photo_data:
            return StreamingResponse(
                io.BytesIO(photo_data),
                media_type="image/jpeg",
                headers={"Content-Disposition": f"inline; filename={person_name}.jpg"}
            )
        else:
            raise HTTPException(status_code=404, detail="Photo not found for this person")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo for {person_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/face-recognition/settings/confidence-threshold")
async def update_confidence_threshold(threshold: float):
    """Update the confidence threshold for face recognition"""
    try:
        result = face_engine.update_confidence_threshold(threshold)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": result["message"],
                    "old_threshold": result["old_threshold"],
                    "new_threshold": result["new_threshold"]
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Invalid threshold"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating confidence threshold: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/doorbell/ring")
async def doorbell_ring(
    image: UploadFile = File(...),
    auto_open: bool = Form(True)
):
    """Handle doorbell ring with automatic face recognition and door opening"""
    try:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_data = await image.read()
        recognition_result = face_engine.recognize_face(image_data)
        
        if not recognition_result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "doorbell_event": "ring",
                    "auto_open": False,
                    "reason": "Face recognition failed",
                    "recognition_error": recognition_result.get("error"),
                    "timestamp": recognition_result.get("timestamp")
                }
            )
        
        # Check for recognized persons (any known person can open door)
        recognized_persons = [
            p for p in recognition_result["recognized_persons"] 
            if p["name"] != "Unknown" and p["access_level"] in ["standard", "admin", "guest"]
        ]
        
        door_opened = False
        recognized_person = None
        
        if recognized_persons and auto_open:
            person = recognized_persons[0]
            recognized_person = person["name"]
            
            door_result = await control_door_for_person(person)
            door_opened = door_result["success"]
            
            logger.info(f"Doorbell: Recognized {recognized_person} (confidence: {person['confidence']:.2f}), "
                       f"Door {'opened' if door_opened else 'failed to open'}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "doorbell_event": "ring",
                "auto_open": door_opened,
                "recognized_person": recognized_person,
                "confidence": recognized_persons[0]["confidence"] if recognized_persons else 0.0,
                "faces_detected": recognition_result["faces_detected"],
                "all_recognized_persons": recognized_persons,
                "timestamp": recognition_result.get("timestamp")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling doorbell ring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def handle_doorbell_recognition(recognized_persons: List[Dict]) -> Dict:
    """Handle doorbell recognition logic"""
    authorized_persons = [
        p for p in recognized_persons 
        if p["name"] != "Unknown" and p["access_level"] in ["standard", "admin", "guest"]
    ]
    
    if authorized_persons:
        person = authorized_persons[0]
        door_result = await control_door_for_person(person)
        
        return {
            "action": "door_opened" if door_result["success"] else "door_open_failed",
            "person": person["name"],
            "confidence": person["confidence"],
            "access_level": person["access_level"]
        }
    else:
        return {
            "action": "access_denied",
            "reason": "No authorized persons recognized"
        }

async def control_door_for_person(person: Dict) -> Dict:
    """Control door opening for a recognized person"""
    try:
        door_state = device_sim.get_device_state("door_front")
        
        if door_state and not door_state.get("locked", True):
            return {
                "success": True,
                "message": "Door is already unlocked",
                "action": "already_open"
            }
        
        update_result = device_sim.update_device_state("door_front", {"locked": False})
        
        if update_result:
            logger.info(f"Door unlocked for {person['name']} (access level: {person['access_level']})")
            return {
                "success": True,
                "message": f"Door unlocked for {person['name']}",
                "action": "door_unlocked"
            }
        else:
            logger.error(f"Failed to unlock door for {person['name']}")
            return {
                "success": False,
                "message": "Failed to unlock door",
                "action": "unlock_failed"
            }
            
    except Exception as e:
        logger.error(f"Error controlling door for {person['name']}: {str(e)}")
        return {
            "success": False,
            "message": f"Door control error: {str(e)}",
            "action": "control_error"
        }

@router.get("/face-recognition/status")
async def get_face_recognition_status():
    """Get the current status of the face recognition system"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "system_status": "operational",
                "confidence_threshold": face_engine.confidence_threshold,
                "known_persons_count": len(face_engine.known_face_names),
                "engine_info": {
                    "face_recognition_library": "face_recognition",
                    "opencv_backend": "available",
                    "storage_path": str(face_engine.known_faces_dir)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting face recognition status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/doorbell/camera/stream")
async def camera_stream():
    """Live camera stream for doorbell"""
    def generate_frames():
        # Initialize camera (prioritize USB camera - Camera 1 for better quality)
        for camera_index in [1, 0, 2]:
            try:
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    break
            except:
                continue
        else:
            # If no camera available, create a dummy frame
            cap = None
        
        try:
            while True:
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                else:
                    # Create a dummy frame if no camera
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "No Camera Available", (50, 240), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Resize frame for better performance
                frame = cv2.resize(frame, (640, 480))
                
                # Encode frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Small delay to control frame rate
                time.sleep(0.1)  # ~10 FPS
                
        except GeneratorExit:
            pass
        finally:
            if cap:
                cap.release()
    
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.post("/doorbell/camera/capture-and-recognize")
async def capture_and_recognize():
    """Capture current frame from camera and perform face recognition"""
    try:
        # Initialize camera (prioritize USB camera - Camera 1 for better quality)
        cap = None
        for camera_index in [1, 0, 2]:
            try:
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    break
            except:
                continue
        
        if not cap or not cap.isOpened():
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "No camera available"}
            )
        
        # Capture frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to capture frame"}
            )
        
        # Android phone camera optimization
        # Phone cameras often need special handling for proper face detection
        
        # Log original frame info for debugging
        logger.info(f"📱 Android camera frame: {frame.shape}, dtype: {frame.dtype}")
        
        # Ensure proper color space (some Android cameras send different formats)
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # Try different color space conversions for Android compatibility
            try:
                # First, ensure we have BGR format (OpenCV standard)
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                # Gentle resize for optimal face detection (Android cameras are high-res)
                height, width = frame.shape[:2]
                if width > 800 or height > 600:
                    scale = min(800/width, 600/height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                
                # Enhance image for better face detection on phone cameras
                # Slight contrast enhancement for better face boundaries
                frame = cv2.convertScaleAbs(frame, alpha=1.05, beta=5)
                
                # Use minimal JPEG compression for phone camera compatibility
                encode_params = [
                    cv2.IMWRITE_JPEG_QUALITY, 95,  # High quality for phone cameras
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1,  # Optimize encoding
                ]
                _, buffer = cv2.imencode('.jpg', frame, encode_params)
                
                logger.info(f"📱 Processed frame: {frame.shape}, compressed size: {len(buffer)}")
                
            except Exception as e:
                logger.error(f"📱 Android camera processing error: {e}")
                # Fallback to basic encoding
                _, buffer = cv2.imencode('.jpg', frame)
        else:
            logger.error(f"📱 Unexpected frame format: {frame.shape}")
            _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()
        
        # Perform face recognition
        result = face_engine.recognize_face(image_bytes)
        
        # Debug logging for live camera
        logger.info(f"🎥 Live camera recognition result: {result}")
        
        if not result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "faces_detected": 0,
                    "recognized_persons": [],
                    "doorbell_response": None,
                    "error": result.get("error")
                }
            )
        
        # Handle doorbell response for recognized persons
        doorbell_response = None
        door_opened = False
        
        if result["recognized_persons"]:
            doorbell_response = await handle_doorbell_recognition(result["recognized_persons"])
            door_opened = doorbell_response.get("action") == "door_opened"
        
        # Convert frame to base64 for frontend display
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        response_data = {
            "success": True,
            "faces_detected": result["faces_detected"],
            "recognized_persons": result["recognized_persons"],
            "doorbell_response": doorbell_response,
            "door_opened": door_opened,
            "timestamp": result.get("timestamp"),
            "captured_image": f"data:image/jpeg;base64,{frame_base64}"
        }
        
        logger.info(f"Live camera recognition: {result['faces_detected']} faces, door_opened: {door_opened}")
        return JSONResponse(status_code=200, content=response_data)
        
    except Exception as e:
        logger.error(f"Error in live camera recognition: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Internal server error: {str(e)}"}
        )

@router.post("/doorbell/camera/start-monitoring")
async def start_camera_monitoring():
    """Start continuous camera monitoring for face recognition"""
    try:
        # This could be enhanced to run continuous monitoring in background
        # For now, return success and let frontend poll the capture endpoint
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Camera monitoring started",
                "monitoring_active": True
            }
        )
    except Exception as e:
        logger.error(f"Error starting camera monitoring: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to start monitoring: {str(e)}"}
        )

@router.post("/doorbell/camera/stop-monitoring")
async def stop_camera_monitoring():
    """Stop continuous camera monitoring"""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Camera monitoring stopped",
                "monitoring_active": False
            }
        )
    except Exception as e:
        logger.error(f"Error stopping camera monitoring: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to stop monitoring: {str(e)}"}
        ) 