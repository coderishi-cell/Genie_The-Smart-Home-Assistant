import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.device_simulator import device_simulator
from core.proactive_engine import proactive_engine
from typing import Dict, Any

router = APIRouter()

class DeviceUpdateRequest(BaseModel):
    device_id: str
    updates: Dict[str, Any]

class SceneRequest(BaseModel):
    scene_name: str

class DeviceResponse(BaseModel):
    device_id: str
    state: Dict[str, Any]
    status: str

class AllDevicesResponse(BaseModel):
    devices: Dict[str, Dict[str, Any]]
    status: str

class SceneResponse(BaseModel):
    scene_name: str
    devices: Dict[str, Dict[str, Any]]
    status: str

@router.get("/devices", response_model=AllDevicesResponse)
async def get_all_devices():
    """Get all device states"""
    try:
        devices = device_simulator.get_all_device_states()
        return AllDevicesResponse(
            devices=devices,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving devices: {str(e)}")

@router.get("/device/{device_id}")
async def get_device(device_id: str):
    """Get a specific device state"""
    try:
        device_state = device_simulator.get_device_state(device_id)
        if not device_state:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        return DeviceResponse(
            device_id=device_id,
            state=device_state,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving device: {str(e)}")

@router.post("/device/update", response_model=DeviceResponse)
async def update_device(request: DeviceUpdateRequest):
    """Update a specific device state"""
    try:
        updated_state = device_simulator.update_device_state(
            request.device_id, 
            request.updates
        )
        
        # Log user behavior for learning
        proactive_engine.log_user_action(
            user_id="user_via_api",  # Default user ID for API interactions
            device_id=request.device_id,
            action_type="device_control",
            action_data=request.updates
        )
        
        return DeviceResponse(
            device_id=request.device_id,
            state=updated_state,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating device: {str(e)}")

@router.post("/device/scene", response_model=SceneResponse)
async def apply_scene(request: SceneRequest):
    """Apply a predefined scene that affects multiple devices"""
    try:
        updated_devices = device_simulator.apply_scene(request.scene_name)
        
        # Log scene application for learning
        proactive_engine.log_user_action(
            user_id="user_via_api",
            device_id="scene_controller",
            action_type="scene_application",
            action_data={"scene_name": request.scene_name}
        )
        
        return SceneResponse(
            scene_name=request.scene_name,
            devices=updated_devices,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying scene: {str(e)}")

@router.get("/scenes")
async def get_available_scenes():
    """Get list of available scenes"""
    scenes = [
        "Movie Mode",
        "Good Morning", 
        "Relax",
        "Energetic",
        "Focus",
        "Sleep"
    ]
    return {"scenes": scenes, "status": "success"} 