import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.agent_controller import get_gemini_response

router = APIRouter()

class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    response: str
    status: str
    device_changes: Optional[Dict[str, Any]] = None

@router.post("/talk", response_model=MessageResponse)
async def talk_to_genie(request: MessageRequest):
    """
    Endpoint to communicate with Genie AI using Gemini LLM and execute device commands
    """
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get response from Gemini and execute any device commands
        genie_response, device_changes = await get_gemini_response(request.message)
        
        return MessageResponse(
            response=genie_response,
            status="success",
            device_changes=device_changes
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error communicating with Genie: {str(e)}"
        ) 