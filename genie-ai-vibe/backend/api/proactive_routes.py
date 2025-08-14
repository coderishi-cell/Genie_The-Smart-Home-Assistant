import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from core.proactive_engine import proactive_engine
from core.weather_service import weather_service
from core.advanced_automation import advanced_automation
from core.smart_mood_integration import smart_mood_integration
from core.device_simulator import device_simulator
from db import db_handler

router = APIRouter()

class UserActionRequest(BaseModel):
    user_id: str
    device_id: str
    action_type: str
    action_data: Dict[str, Any]

class AutomationControlRequest(BaseModel):
    action: str  # "start" or "stop"

class UserFeedbackRequest(BaseModel):
    automation_id: int
    feedback: str  # "good", "bad", "unnecessary"
    comment: Optional[str] = None

class AutomationStatusResponse(BaseModel):
    is_running: bool
    check_interval_minutes: int
    recent_decisions: List[Dict[str, Any]]
    total_learned_patterns: int
    total_preferences: int
    last_weather_check: Optional[str]
    last_time_check: Optional[str]

@router.post("/automation/control")
async def control_automation(request: AutomationControlRequest):
    """Start or stop the proactive automation system"""
    try:
        if request.action == "start":
            proactive_engine.start_proactive_automation()
            return {
                "status": "success",
                "message": "Proactive automation started",
                "is_running": proactive_engine.is_running
            }
        elif request.action == "stop":
            proactive_engine.stop_proactive_automation()
            return {
                "status": "success",
                "message": "Proactive automation stopped",
                "is_running": proactive_engine.is_running
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'start' or 'stop'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error controlling automation: {str(e)}")

@router.get("/automation/status", response_model=AutomationStatusResponse)
async def get_automation_status():
    """Get current status of the proactive automation system"""
    try:
        status = proactive_engine.get_automation_status()
        return AutomationStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automation status: {str(e)}")

@router.post("/automation/log-action")
async def log_user_action(request: UserActionRequest):
    """Log a user action for learning purposes"""
    try:
        proactive_engine.log_user_action(
            user_id=request.user_id,
            device_id=request.device_id,
            action_type=request.action_type,
            action_data=request.action_data
        )
        
        return {
            "status": "success",
            "message": "User action logged successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging user action: {str(e)}")

@router.get("/automation/patterns")
async def get_user_patterns():
    """Get learned user behavior patterns"""
    try:
        patterns = db_handler.get_user_behavior_patterns()
        return {
            "status": "success",
            "patterns": patterns,
            "total_patterns": len(patterns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user patterns: {str(e)}")

@router.get("/automation/decisions")
async def get_automation_decisions(limit: int = 20):
    """Get recent automation decisions"""
    try:
        decisions = db_handler.get_automation_history(limit=limit)
        return {
            "status": "success",
            "decisions": decisions,
            "total_decisions": len(decisions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving automation decisions: {str(e)}")

@router.get("/automation/preferences")
async def get_user_preferences():
    """Get learned user preferences"""
    try:
        preferences = db_handler.get_user_preferences()
        return {
            "status": "success",
            "preferences": preferences,
            "total_preferences": len(preferences)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user preferences: {str(e)}")

@router.post("/automation/feedback")
async def provide_automation_feedback(request: UserFeedbackRequest):
    """Provide feedback on automation decisions"""
    try:
        # Update the automation decision with user feedback
        # This would require updating the database handler to support feedback updates
        # For now, we'll just log it
        
        print(f"📝 User feedback received for automation {request.automation_id}: {request.feedback}")
        if request.comment:
            print(f"   Comment: {request.comment}")
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")

@router.get("/weather/current")
async def get_current_weather():
    """Get current weather data"""
    try:
        weather_data = weather_service.get_current_weather()
        if weather_data:
            return {
                "status": "success",
                "weather": weather_data
            }
        else:
            raise HTTPException(status_code=503, detail="Weather data unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting weather data: {str(e)}")

@router.get("/weather/recommendations")
async def get_weather_recommendations():
    """Get comfort recommendations based on current weather"""
    try:
        weather_data = weather_service.get_current_weather()
        if weather_data:
            recommendations = weather_service.get_comfort_recommendations(weather_data)
            return {
                "status": "success",
                "recommendations": recommendations,
                "weather_context": weather_data
            }
        else:
            raise HTTPException(status_code=503, detail="Weather data unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting weather recommendations: {str(e)}")

@router.get("/weather/extreme-check")
async def check_extreme_weather():
    """Check if current weather conditions are extreme"""
    try:
        weather_data = weather_service.get_current_weather()
        if weather_data:
            extreme_check = weather_service.is_weather_extreme(weather_data)
            return {
                "status": "success",
                "extreme_weather": extreme_check,
                "weather_context": weather_data
            }
        else:
            raise HTTPException(status_code=503, detail="Weather data unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking extreme weather: {str(e)}")

@router.get("/automation/insights")
async def get_automation_insights():
    """Get insights and analytics about automation patterns"""
    try:
        # Get various analytics
        patterns = db_handler.get_user_behavior_patterns()
        decisions = db_handler.get_automation_history(limit=100)
        preferences = db_handler.get_user_preferences()
        
        # Calculate some basic insights
        device_usage = {}
        for pattern in patterns:
            device_id = pattern['device_id']
            if device_id not in device_usage:
                device_usage[device_id] = 0
            device_usage[device_id] += 1
        
        # Most active hours
        hour_activity = {}
        for pattern in patterns:
            hour = pattern['time_of_day']
            if hour not in hour_activity:
                hour_activity[hour] = 0
            hour_activity[hour] += 1
        
        # Automation success rate
        successful_decisions = sum(1 for d in decisions if d.get('success', True))
        success_rate = (successful_decisions / len(decisions) * 100) if decisions else 0
        
        return {
            "status": "success",
            "insights": {
                "total_patterns": len(patterns),
                "total_decisions": len(decisions),
                "total_preferences": len(preferences),
                "automation_success_rate": round(success_rate, 2),
                "most_used_devices": sorted(device_usage.items(), key=lambda x: x[1], reverse=True)[:5],
                "most_active_hours": sorted(hour_activity.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting automation insights: {str(e)}")

@router.get("/automation/advanced-insights")
async def get_advanced_automation_insights():
    """Get insights about advanced automation features"""
    try:
        insights = advanced_automation.get_automation_insights()
        mood_insights = smart_mood_integration.get_mood_insights()
        
        return {
            "status": "success",
            "advanced_automation": insights,
            "mood_integration": mood_insights,
            "total_advanced_features": insights.get('features_count', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting advanced insights: {str(e)}")

@router.post("/automation/suggest-mood")
async def suggest_optimal_mood():
    """Get AI-powered mood suggestion based on current context"""
    try:
        suggestion = await smart_mood_integration.suggest_optimal_mood({})
        
        if suggestion:
            return {
                "status": "success",
                "mood_suggestion": suggestion
            }
        else:
            return {
                "status": "no_suggestion",
                "message": "No strong mood suggestion at this time"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting mood: {str(e)}")

@router.post("/automation/apply-mood-automation")
async def apply_mood_automation(mood: str = Query(..., description="The mood to apply")):
    """Apply mood-based automation"""
    try:
        decisions = await smart_mood_integration.mood_based_automation(mood)
        
        # Execute the decisions through the proactive engine
        executed_count = 0
        for decision in decisions:
            try:
                device_simulator.update_device_state(decision['device_id'], decision['action'])
                executed_count += 1
            except Exception as e:
                print(f"Error executing mood automation: {e}")
        
        return {
            "status": "success",
            "mood": mood,
            "decisions_executed": executed_count,
            "total_decisions": len(decisions),
            "message": f"Applied {executed_count} mood-based automations for {mood}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying mood automation: {str(e)}")

@router.get("/automation/energy-analysis")
async def get_energy_analysis():
    """Get energy usage analysis and optimization suggestions"""
    try:
        current_states = device_simulator.get_all_device_states()
        energy_decisions = await advanced_automation.energy_optimization_automation(current_states)
        
        # Calculate energy usage estimate
        lights_on = sum(1 for device in current_states.values() 
                       if device.get('type') == 'light' and device.get('on', False))
        ac_running = any(device.get('type') == 'ac' and device.get('on', False) 
                        for device in current_states.values())
        
        estimated_usage = lights_on * 10 + (50 if ac_running else 0)
        
        return {
            "status": "success",
            "energy_analysis": {
                "estimated_usage_watts": estimated_usage,
                "lights_on_count": lights_on,
                "ac_running": ac_running,
                "optimization_suggestions": len(energy_decisions),
                "potential_savings": sum(10 for d in energy_decisions if 'light' in d.get('device_id', ''))
            },
            "optimization_decisions": energy_decisions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing energy: {str(e)}")

@router.get("/automation/sleep-optimization")
async def get_sleep_optimization():
    """Get sleep optimization status and suggestions"""
    try:
        current_states = device_simulator.get_all_device_states()
        sleep_decisions = await advanced_automation.sleep_optimization_automation(current_states)
        
        return {
            "status": "success",
            "sleep_optimization": {
                "active_optimizations": len(sleep_decisions),
                "decisions": sleep_decisions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sleep optimization: {str(e)}")

@router.delete("/automation/reset-learning")
async def reset_learning_data():
    """Reset all learned patterns and preferences (use with caution)"""
    try:
        # This would require additional database functions to clear learning data
        # For now, we'll just return a message
        return {
            "status": "success",
            "message": "Learning data reset functionality not implemented yet",
            "warning": "This operation would clear all learned patterns and preferences"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting learning data: {str(e)}")

# Auto-start the proactive automation when the module is imported
# This ensures it starts automatically when the server starts
try:
    if not proactive_engine.is_running:
        proactive_engine.start_proactive_automation()
        print("🚀 Proactive automation auto-started with API routes")
except Exception as e:
    print(f"❌ Error auto-starting proactive automation: {e}") 