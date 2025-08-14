from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict, List
import io
import json
import logging
from pydantic import BaseModel

from core.face_recognition_engine import FaceRecognitionEngine
from core.device_simulator import DeviceSimulator

logger = logging.getLogger(__name__)

# Initialize face recognition engine
face_engine = FaceRecognitionEngine()

# Initialize device simulator for door control
device_sim = DeviceSimulator()

router = APIRouter()

# Pydantic models for request/response
class PersonMetadata(BaseModel):
    access_level: str = "standard"  # standard, admin, guest
    notes: str = ""

class RecognitionResult(BaseModel):
    success: bool
    faces_detected: int
    recognized_persons: List[Dict]
    timestamp: Optional[str] = None
    error: Optional[str] = None

class PersonInfo(BaseModel):
    name: str
    access_level: str
    added_date: str
    notes: str
    has_photo: bool

class DoorbellEvent(BaseModel):
    auto_open: bool = False
    recognized_person: Optional[str] = None
    confidence: float = 0.0
    timestamp: str

@router.post("/face-recognition/add-person")
async def add_known_person(
    name: str = Form(...),
    photo: UploadFile = File(...),
    access_level: str = Form("standard"),
    notes: str = Form("")
):
    """
    Add a new known person to the face recognition database
    
    Args:
        name: Person's name/identifier
        photo: Photo file containing the person's face
        access_level: Access level (standard, admin, guest)
        notes: Additional notes about the person
    """
    try:
        # Validate file type
        if not photo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read photo data
        photo_data = await photo.read()
        
        # Prepare metadata
        metadata = {
            "access_level": access_level,
            "notes": notes
        }
        
        # Add person to face recognition engine
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

@router.post("/face-recognition/recognize", response_model=RecognitionResult)
async def recognize_faces(
    image: UploadFile = File(...),
    doorbell_mode: bool = Form(False)
):
    """
    Recognize faces in the provided image
    
    Args:
        image: Image file to analyze
        doorbell_mode: If True, automatically open door for recognized persons with appropriate access
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Perform face recognition
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
        
        logger.info(f"Face recognition completed: {result['faces_detected']} faces detected, "
                   f"{len([p for p in result['recognized_persons'] if p['name'] != 'Unknown'])} recognized")
        
        return JSONResponse(status_code=200, content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in face recognition: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/face-recognition/persons")
async def list_known_persons():
    """
    List all known persons in the face recognition database
    """
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
    """
    Remove a person from the face recognition database
    
    Args:
        person_name: Name of the person to remove
    """
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
    """
    Get the photo of a known person
    
    Args:
        person_name: Name of the person
    """
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
    """
    Update the confidence threshold for face recognition
    
    Args:
        threshold: New threshold value (0.0 to 1.0)
    """
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
    """
    Handle doorbell ring with automatic face recognition and door opening
    
    Args:
        image: Image from doorbell camera
        auto_open: Whether to automatically open door for recognized persons
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Perform face recognition
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
        
        # Check for recognized persons
        recognized_persons = [
            p for p in recognition_result["recognized_persons"] 
            if p["name"] != "Unknown" and p["access_level"] in ["standard", "admin"]
        ]
        
        door_opened = False
        recognized_person = None
        
        if recognized_persons and auto_open:
            # Open door for the first recognized person with appropriate access
            person = recognized_persons[0]
            recognized_person = person["name"]
            
            # Control the door device
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
    """
    Handle doorbell recognition logic
    
    Args:
        recognized_persons: List of recognized persons from face recognition
        
    Returns:
        Dict with doorbell response information
    """
    authorized_persons = [
        p for p in recognized_persons 
        if p["name"] != "Unknown" and p["access_level"] in ["standard", "admin"]
    ]
    
    if authorized_persons:
        # Open door for the first authorized person
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
    """
    Control door opening for a recognized person
    
    Args:
        person: Dictionary containing person information
        
    Returns:
        Dict with door control result
    """
    try:
        # Get current door state
        door_state = device_sim.get_device_state("door_front")
        
        if door_state and not door_state.get("locked", True):
            return {
                "success": True,
                "message": "Door is already unlocked",
                "action": "already_open"
            }
        
        # Unlock the door
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
    """
    Get the current status of the face recognition system
    """
    try:
        persons_result = face_engine.list_known_persons()
        
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