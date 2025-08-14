import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db_handler
from core.device_simulator import device_simulator
from core.weather_service import weather_service

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SmartMoodIntegration:
    def __init__(self):
        self.mood_learning_enabled = True
        self.context_awareness = True
        self.auto_mood_suggestions = True
        
        print("🎭 Smart Mood Integration initialized!")

    async def suggest_optimal_mood(self, current_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest the optimal mood based on current context"""
        try:
            current_time = datetime.now()
            weather_data = weather_service.get_current_weather()
            
            # Build context for LLM
            context = {
                'time': {
                    'hour': current_time.hour,
                    'day_of_week': current_time.strftime('%A'),
                },
                'weather': weather_data,
                'current_devices': device_simulator.get_all_device_states()
            }
            
            # Get mood suggestion from LLM
            mood_suggestion = await self._get_llm_mood_suggestion(context)
            
            if mood_suggestion:
                return {
                    'suggested_mood': mood_suggestion['mood'],
                    'reason': mood_suggestion['reason'],
                    'confidence': mood_suggestion['confidence'],
                    'context': context
                }
            
        except Exception as e:
            print(f"❌ Error suggesting optimal mood: {e}")
        
        return None

    async def mood_based_automation(self, current_mood: str) -> List[Dict[str, Any]]:
        """Perform automation based on current mood"""
        decisions = []
        
        try:
            current_time = datetime.now()
            weather_data = weather_service.get_current_weather()
            current_states = device_simulator.get_all_device_states()
            
            # Get mood-specific optimizations
            optimizations = self._get_mood_optimizations(current_mood, weather_data, current_time)
            
            for device_id, settings in optimizations.items():
                if device_id in current_states:
                    current_device = current_states[device_id]
                    if self._needs_adjustment(current_device, settings):
                        decisions.append({
                            'type': 'mood_optimization',
                            'device_id': device_id,
                            'action': settings,
                            'reason': f'Mood-based optimization for {current_mood}',
                            'mood': current_mood,
                            'confidence': 0.8
                        })
            
        except Exception as e:
            print(f"❌ Error in mood-based automation: {e}")
        
        return decisions

    def _get_mood_optimizations(self, mood: str, weather_data: Dict[str, Any], 
                               current_time: datetime) -> Dict[str, Dict[str, Any]]:
        """Get device optimizations for specific mood"""
        optimizations = {}
        hour = current_time.hour
        
        if mood == 'Energetic':
            optimizations['light_living_room'] = {'on': True, 'brightness': 90, 'color': '#00FF7F'}
            optimizations['light_kitchen'] = {'on': True, 'brightness': 85, 'color': '#FFFFFF'}
            optimizations['music_player'] = {'playing': True, 'volume': 60}
            
            if weather_data and weather_data.get('temperature', 25) > 25:
                optimizations['ac_main'] = {'on': True, 'temperature': 21}
            
        elif mood == 'Relax':
            optimizations['light_living_room'] = {'on': True, 'brightness': 50, 'color': '#FF6B6B'}
            optimizations['light_bedroom'] = {'on': True, 'brightness': 40, 'color': '#FFB6C1'}
            optimizations['music_player'] = {'playing': True, 'volume': 30}
            optimizations['ac_main'] = {'on': True, 'temperature': 23}
            
        elif mood == 'Focus':
            optimizations['light_living_room'] = {'on': True, 'brightness': 80, 'color': '#F0F8FF'}
            optimizations['light_kitchen'] = {'on': True, 'brightness': 75, 'color': '#FFFFFF'}
            optimizations['music_player'] = {'playing': True, 'volume': 25}
            optimizations['ac_main'] = {'on': True, 'temperature': 22}
        
        # Evening adjustments
        if hour >= 20:
            for device_id in optimizations:
                if device_id.startswith('light_'):
                    optimizations[device_id]['brightness'] = max(30, optimizations[device_id].get('brightness', 50) - 20)
        
        return optimizations

    def _needs_adjustment(self, current_device: Dict[str, Any], 
                         target_settings: Dict[str, Any]) -> bool:
        """Check if device needs adjustment"""
        for key, value in target_settings.items():
            current_value = current_device.get(key)
            
            if key == 'brightness' and isinstance(current_value, (int, float)):
                if abs(current_value - value) > 15:
                    return True
            elif key == 'temperature' and isinstance(current_value, (int, float)):
                if abs(current_value - value) > 2:
                    return True
            elif current_value != value:
                return True
        
        return False

    async def _get_llm_mood_suggestion(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use LLM to suggest optimal mood"""
        try:
            if not GEMINI_API_KEY:
                return None
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
You are Genie, suggesting the best mood for current context.

CONTEXT:
- Time: {context['time']['hour']}:00 on {context['time']['day_of_week']}
- Weather: {context['weather'].get('condition', 'Unknown')} at {context['weather'].get('temperature', 'Unknown')}°C

MOODS: Energetic, Relax, Focus, Sleep

GUIDELINES:
- Morning = Energetic, Evening = Relax, Night = Sleep
- Rainy = Relax, Sunny = Energetic, Hot = Focus (cool)

Respond JSON: {{"mood": "name", "reason": "explanation", "confidence": 0.8}}
"""
            
            response = model.generate_content(prompt)
            
            if response.text:
                try:
                    import json
                    result = json.loads(response.text.strip())
                    return result
                except json.JSONDecodeError:
                    text = response.text.lower()
                    if 'energetic' in text:
                        return {'mood': 'Energetic', 'reason': 'LLM suggested energetic', 'confidence': 0.7}
                    elif 'relax' in text:
                        return {'mood': 'Relax', 'reason': 'LLM suggested relax', 'confidence': 0.7}
                    elif 'focus' in text:
                        return {'mood': 'Focus', 'reason': 'LLM suggested focus', 'confidence': 0.7}
            
        except Exception as e:
            print(f"❌ Error in LLM mood suggestion: {e}")
        
        return None

    def get_mood_insights(self) -> Dict[str, Any]:
        """Get insights about mood integration"""
        return {
            'context_awareness_active': self.context_awareness,
            'auto_suggestions_active': self.auto_mood_suggestions,
            'mood_learning_enabled': self.mood_learning_enabled
        }

# Global instance
smart_mood_integration = SmartMoodIntegration() 