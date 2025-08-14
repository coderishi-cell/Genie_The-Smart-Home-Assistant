import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.mood_engine import mood_engine
from typing import Dict, Any

router = APIRouter()

class MoodRequest(BaseModel):
    mood_name: str

class MoodResponse(BaseModel):
    mood_name: str
    theme_vars: Dict[str, Any]
    device_states: Dict[str, Dict[str, Any]]
    status: str

class MoodPreviewResponse(BaseModel):
    mood_name: str
    theme_vars: Dict[str, Any]
    status: str

class AvailableMoodsResponse(BaseModel):
    moods: list
    current_mood: str
    status: str

@router.post("/mood/set", response_model=MoodResponse)
async def set_mood(request: MoodRequest):
    """Set a new mood, which applies a scene and returns theme variables"""
    try:
        theme_vars, device_states = mood_engine.set_mood(request.mood_name)
        
        return MoodResponse(
            mood_name=request.mood_name,
            theme_vars=theme_vars,
            device_states=device_states,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting mood: {str(e)}")

@router.get("/mood/preview/{mood_name}", response_model=MoodPreviewResponse)
async def preview_mood(mood_name: str):
    """Get theme variables for a mood without applying it"""
    try:
        theme_vars = mood_engine.get_mood_preview(mood_name)
        
        return MoodPreviewResponse(
            mood_name=mood_name,
            theme_vars=theme_vars,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing mood: {str(e)}")

@router.get("/moods", response_model=AvailableMoodsResponse)
async def get_available_moods():
    """Get list of available moods and current mood"""
    try:
        moods = mood_engine.get_available_moods()
        current_mood = mood_engine.get_current_mood()
        
        return AvailableMoodsResponse(
            moods=moods,
            current_mood=current_mood,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving moods: {str(e)}")

@router.post("/mood/apply", response_model=MoodResponse)
async def apply_mood(request: MoodRequest):
    """Apply a mood (alias for set_mood for compatibility)"""
    try:
        theme_vars, device_states = mood_engine.set_mood(request.mood_name)
        
        return MoodResponse(
            mood_name=request.mood_name,
            theme_vars=theme_vars,
            device_states=device_states,
            status="success"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying mood: {str(e)}")

@router.get("/mood/current")
async def get_current_mood():
    """Get the currently active mood"""
    try:
        current_mood = mood_engine.get_current_mood()
        theme_vars = mood_engine.get_mood_preview(current_mood)
        
        return {
            "current_mood": current_mood,
            "theme_vars": theme_vars,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving current mood: {str(e)}") 