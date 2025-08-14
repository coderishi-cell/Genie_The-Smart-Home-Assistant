import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import google.generativeai as genai
from collections import defaultdict
import threading
import time
import statistics

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db_handler
from core.device_simulator import device_simulator
from core.weather_service import weather_service
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AdvancedAutomation:
    def __init__(self):
        self.energy_savings_enabled = True
        self.occupancy_simulation = True
        self.predictive_mode = True
        self.sleep_optimization = True
        self.security_intelligence = True
        self.energy_usage_log = []
        self.occupancy_patterns = {}
        self.sleep_optimization_data = {}
        self.security_alerts = []
        self.guest_mode_active = False
        self.seasonal_preferences = {}
        self.activity_recognition = {}
        self.predictive_schedule = {}
        
        print("🚀 Advanced Automation features initialized!")

    async def energy_optimization_automation(self, current_states: Dict[str, Any], 
                                           weather_data: Dict[str, Any] = None) -> List[Dict]:
        """Intelligent energy optimization based on usage patterns and weather"""
        decisions = []
        current_time = datetime.now()
        
        try:
            # Get energy usage patterns
            energy_insights = self._analyze_energy_patterns(current_states)
            
            # Peak hours energy saving (2-6 PM)
            if 14 <= current_time.hour <= 18:
                decisions.extend(self._peak_hours_optimization(current_states, energy_insights))
            
            # Night energy saving (11 PM - 6 AM)
            elif current_time.hour >= 23 or current_time.hour <= 6:
                decisions.extend(self._night_energy_optimization(current_states))
            
            # Weather-based energy optimization
            if weather_data:
                decisions.extend(self._weather_energy_optimization(current_states, weather_data))
            
            # Idle device detection
            decisions.extend(self._idle_device_optimization(current_states))
            
        except Exception as e:
            print(f"❌ Error in energy optimization: {e}")
        
        return decisions

    async def occupancy_based_automation(self, face_recognition_data: Dict[str, Any] = None) -> List[Dict]:
        """Smart automation based on room occupancy and user presence"""
        decisions = []
        current_time = datetime.now()
        current_states = device_simulator.get_all_device_states()
        
        try:
            # Simulate occupancy detection (in real system, this would use sensors/cameras)
            occupancy_status = self._detect_occupancy(face_recognition_data)
            
            # Nobody home - energy saving mode
            if not occupancy_status['anyone_home']:
                decisions.extend(self._away_mode_automation(current_states))
            
            # Someone just arrived home
            elif occupancy_status['just_arrived']:
                decisions.extend(self._arrival_automation(current_states, occupancy_status))
            
            # Room-specific automation based on presence
            for room, occupied in occupancy_status['rooms'].items():
                if not occupied:
                    decisions.extend(self._empty_room_automation(room, current_states))
                else:
                    decisions.extend(self._occupied_room_automation(room, current_states, occupancy_status))
            
        except Exception as e:
            print(f"❌ Error in occupancy automation: {e}")
        
        return decisions

    async def predictive_scheduling_automation(self) -> List[Dict]:
        """Predict user needs and prepare environment in advance"""
        decisions = []
        current_time = datetime.now()
        current_states = device_simulator.get_all_device_states()
        
        try:
            # Get user behavior patterns for prediction
            patterns = db_handler.get_user_behavior_patterns()
            
            # Predict upcoming activities (next 1-2 hours)
            predictions = self._predict_upcoming_activities(patterns, current_time)
            
            for prediction in predictions:
                if prediction['confidence'] > 0.7:  # High confidence predictions only
                    decisions.extend(self._prepare_for_activity(prediction, current_states))
            
            # Weekend vs weekday predictions
            if current_time.weekday() >= 5:  # Weekend
                decisions.extend(self._weekend_predictions(current_states, current_time))
            else:  # Weekday
                decisions.extend(self._weekday_predictions(current_states, current_time))
            
        except Exception as e:
            print(f"❌ Error in predictive scheduling: {e}")
        
        return decisions

    async def sleep_optimization_automation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Advanced sleep environment optimization"""
        decisions = []
        current_time = datetime.now()
        
        try:
            # Pre-sleep preparation (30-60 minutes before typical bedtime)
            learned_bedtime = self._get_learned_bedtime()
            if learned_bedtime:
                minutes_to_bedtime = self._minutes_until_bedtime(learned_bedtime, current_time)
                
                if 30 <= minutes_to_bedtime <= 60:
                    decisions.extend(self._pre_sleep_preparation(current_states))
                elif 0 <= minutes_to_bedtime <= 30:
                    decisions.extend(self._bedtime_optimization(current_states))
            
            # Sleep quality optimization during night
            if self._is_sleep_hours(current_time):
                decisions.extend(self._sleep_quality_optimization(current_states))
            
            # Wake-up preparation
            learned_wake_time = self._get_learned_wake_time()
            if learned_wake_time:
                minutes_to_wake = self._minutes_until_wake(learned_wake_time, current_time)
                
                if 15 <= minutes_to_wake <= 30:
                    decisions.extend(self._wake_up_preparation(current_states))
            
        except Exception as e:
            print(f"❌ Error in sleep optimization: {e}")
        
        return decisions

    async def security_intelligence_automation(self, current_states: Dict[str, Any] = None, 
                                             face_recognition_data: Dict[str, Any] = None) -> List[Dict]:
        """Intelligent security automation based on patterns and anomalies"""
        decisions = []
        current_time = datetime.now()
        
        if current_states is None:
            current_states = device_simulator.get_all_device_states()
        
        try:
            # Unusual activity detection
            if self._detect_unusual_activity(current_time):
                decisions.extend(self._unusual_activity_response(current_states))
            
            # Auto-security based on time and patterns
            if self._should_auto_arm_security(current_time):
                decisions.extend(self._auto_security_activation(current_states))
            
        except Exception as e:
            print(f"❌ Error in security intelligence: {e}")
        
        return decisions

    async def mood_based_intelligence(self, current_mood: str, weather_data: Dict[str, Any], 
                                    current_states: Dict[str, Any]) -> List[Dict]:
        """Proactive mood-based environment adjustments"""
        decisions = []
        
        try:
            # Mood-weather correlation
            optimal_settings = self._get_mood_weather_optimization(current_mood, weather_data)
            
            for device_id, settings in optimal_settings.items():
                if device_id in current_states:
                    current_device = current_states[device_id]
                    if self._settings_need_adjustment(current_device, settings):
                        decisions.append({
                            'type': 'mood_optimization',
                            'device_id': device_id,
                            'action': settings,
                            'reason': f'Mood-based optimization for {current_mood} mood',
                            'mood_context': current_mood,
                            'weather_context': weather_data
                        })
            
            # Proactive mood suggestions based on weather
            mood_suggestion = self._suggest_mood_for_weather(weather_data)
            if mood_suggestion and mood_suggestion != current_mood:
                decisions.append({
                    'type': 'mood_suggestion',
                    'device_id': 'mood_controller',
                    'action': {'suggested_mood': mood_suggestion},
                    'reason': f'Weather suggests {mood_suggestion} mood',
                    'confidence': 0.8
                })
            
        except Exception as e:
            print(f"❌ Error in mood-based intelligence: {e}")
        
        return decisions

    def _analyze_energy_patterns(self, current_states: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current energy usage patterns"""
        total_lights_on = sum(1 for device in current_states.values() 
                             if device.get('type') == 'light' and device.get('on', False))
        
        total_devices_on = sum(1 for device in current_states.values() 
                              if device.get('on', False))
        
        ac_running = any(device.get('type') == 'ac' and device.get('on', False) 
                        for device in current_states.values())
        
        return {
            'lights_on_count': total_lights_on,
            'total_devices_on': total_devices_on,
            'ac_running': ac_running,
            'estimated_usage': total_lights_on * 10 + (50 if ac_running else 0)  # Simplified calculation
        }

    def _peak_hours_optimization(self, current_states: Dict[str, Any], 
                                energy_insights: Dict[str, Any]) -> List[Dict]:
        """Optimize energy during peak hours"""
        decisions = []
        
        # Reduce non-essential lighting during peak hours
        if energy_insights['lights_on_count'] > 2:
            for device_id, device in current_states.items():
                if (device.get('type') == 'light' and device.get('on', False) and 
                    device_id not in ['light_living_room', 'light_kitchen']):  # Keep essential lights
                    decisions.append({
                        'type': 'peak_energy_optimization',
                        'device_id': device_id,
                        'action': {'brightness': max(30, device.get('brightness', 70) - 20)},
                        'reason': 'Peak hours energy optimization - dimming non-essential lights'
                    })
        
        return decisions

    def _night_energy_optimization(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Optimize energy during night hours"""
        decisions = []
        
        # Turn off unnecessary devices at night
        for device_id, device in current_states.items():
            if device.get('type') == 'light' and device.get('on', False):
                if device_id not in ['light_bedroom']:  # Keep bedroom light for safety
                    decisions.append({
                        'type': 'night_energy_optimization',
                        'device_id': device_id,
                        'action': {'on': False},
                        'reason': 'Night energy optimization - turning off unnecessary lights'
                    })
        
        return decisions

    def _weather_energy_optimization(self, current_states: Dict[str, Any], 
                                   weather_data: Dict[str, Any]) -> List[Dict]:
        """Optimize energy based on weather conditions"""
        decisions = []
        
        # Use natural light when available
        if weather_data.get('condition', '').lower() in ['clear', 'sunny']:
            for device_id, device in current_states.items():
                if (device.get('type') == 'light' and device.get('on', False) and 
                    device.get('brightness', 0) > 60):
                    decisions.append({
                        'type': 'natural_light_optimization',
                        'device_id': device_id,
                        'action': {'brightness': 40},
                        'reason': 'Using natural light to save energy'
                    })
        
        return decisions

    def _idle_device_optimization(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Detect and optimize idle devices"""
        decisions = []
        
        # Turn off music player if no one is home (simplified logic)
        music_device = current_states.get('music_player', {})
        if music_device.get('playing', False):
            # In a real system, this would check actual occupancy
            decisions.append({
                'type': 'idle_device_optimization',
                'device_id': 'music_player',
                'action': {'playing': False},
                'reason': 'Auto-pause music - no activity detected',
                'confidence': 0.6
            })
        
        return decisions

    def _empty_room_automation(self, room: str, current_states: Dict[str, Any]) -> List[Dict]:
        """Automation for empty rooms"""
        decisions = []
        
        # Turn off lights in empty rooms
        room_light_id = f'light_{room}'
        if room_light_id in current_states and current_states[room_light_id].get('on', False):
            decisions.append({
                'type': 'empty_room_optimization',
                'device_id': room_light_id,
                'action': {'on': False},
                'reason': f'Room {room} is empty - turning off lights'
            })
        
        return decisions

    def _occupied_room_automation(self, room: str, current_states: Dict[str, Any], 
                                 occupancy_status: Dict[str, Any]) -> List[Dict]:
        """Automation for occupied rooms"""
        decisions = []
        current_hour = datetime.now().hour
        
        # Ensure appropriate lighting in occupied rooms
        room_light_id = f'light_{room}'
        if room_light_id in current_states:
            current_light = current_states[room_light_id]
            
            # Turn on lights if it's evening/night and room is occupied
            if 18 <= current_hour <= 23 and not current_light.get('on', False):
                decisions.append({
                    'type': 'occupied_room_optimization',
                    'device_id': room_light_id,
                    'action': {'on': True, 'brightness': 70},
                    'reason': f'Room {room} is occupied - providing appropriate lighting'
                })
            
            # Adjust brightness based on time of day
            elif current_light.get('on', False):
                target_brightness = 80 if 6 <= current_hour <= 18 else 50
                if abs(current_light.get('brightness', 70) - target_brightness) > 20:
                    decisions.append({
                        'type': 'occupied_room_optimization',
                        'device_id': room_light_id,
                        'action': {'brightness': target_brightness},
                        'reason': f'Adjusting lighting for occupied room {room}'
                    })
        
        return decisions

    def _detect_occupancy(self, face_recognition_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate occupancy detection"""
        current_hour = datetime.now().hour
        
        # Simulate occupancy based on typical patterns
        likely_home = 6 <= current_hour <= 23  # Assume people are home during these hours
        
        return {
            'anyone_home': likely_home,
            'just_arrived': False,  # Would be detected via face recognition or sensors
            'rooms': {
                'living_room': likely_home and 8 <= current_hour <= 22,
                'kitchen': likely_home and (7 <= current_hour <= 9 or 17 <= current_hour <= 20),
                'bedroom': current_hour >= 22 or current_hour <= 7
            },
            'guest_present': False
        }

    def _away_mode_automation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Automation when nobody is home"""
        decisions = []
        
        # Turn off non-essential devices
        for device_id, device in current_states.items():
            if device.get('type') == 'light' and device.get('on', False):
                decisions.append({
                    'type': 'away_mode',
                    'device_id': device_id,
                    'action': {'on': False},
                    'reason': 'Away mode - turning off lights'
                })
            elif device.get('type') == 'music' and device.get('playing', False):
                decisions.append({
                    'type': 'away_mode',
                    'device_id': device_id,
                    'action': {'playing': False},
                    'reason': 'Away mode - stopping music'
                })
        
        # Activate security
        security_device = current_states.get('security_system', {})
        if not security_device.get('armed', False):
            decisions.append({
                'type': 'away_mode',
                'device_id': 'security_system',
                'action': {'armed': True, 'mode': 'away'},
                'reason': 'Away mode - activating security'
            })
        
        return decisions

    def _arrival_automation(self, current_states: Dict[str, Any], 
                          occupancy_status: Dict[str, Any]) -> List[Dict]:
        """Automation when someone arrives home"""
        decisions = []
        current_hour = datetime.now().hour
        
        # Welcome lighting based on time of day
        if 17 <= current_hour <= 23:  # Evening arrival
            decisions.append({
                'type': 'arrival_welcome',
                'device_id': 'light_living_room',
                'action': {'on': True, 'brightness': 70, 'color': '#FFD700'},
                'reason': 'Welcome home - evening lighting'
            })
        
        # Disable security
        security_device = current_states.get('security_system', {})
        if security_device.get('armed', False):
            decisions.append({
                'type': 'arrival_welcome',
                'device_id': 'security_system',
                'action': {'armed': False, 'mode': 'home'},
                'reason': 'Welcome home - disabling security'
            })
        
        return decisions

    def _predict_upcoming_activities(self, patterns: List[Dict], current_time: datetime) -> List[Dict]:
        """Predict what the user might do in the next 1-2 hours"""
        predictions = []
        
        # Group patterns by hour
        hour_patterns = defaultdict(list)
        for pattern in patterns:
            hour_patterns[pattern['time_of_day']].append(pattern)
        
        # Check next 2 hours
        for hour_offset in [1, 2]:
            target_hour = (current_time.hour + hour_offset) % 24
            if target_hour in hour_patterns:
                common_actions = self._get_common_actions_for_hour(hour_patterns[target_hour])
                for action in common_actions:
                    predictions.append({
                        'predicted_hour': target_hour,
                        'action': action,
                        'confidence': action.get('confidence', 0.5),
                        'time_until': hour_offset * 60  # minutes
                    })
        
        return predictions

    def _get_common_actions_for_hour(self, hour_patterns: List[Dict]) -> List[Dict]:
        """Get the most common actions for a specific hour"""
        action_counts = defaultdict(int)
        
        for pattern in hour_patterns:
            action_key = f"{pattern['device_id']}_{pattern['action_type']}"
            action_counts[action_key] += 1
        
        # Return actions that occur frequently
        common_actions = []
        for action_key, count in action_counts.items():
            if count >= 2:  # Appears at least twice
                device_id, action_type = action_key.split('_', 1)
                common_actions.append({
                    'device_id': device_id,
                    'action_type': action_type,
                    'confidence': min(count / 5, 1.0)  # Max confidence of 1.0
                })
        
        return common_actions

    def _prepare_for_activity(self, prediction: Dict, current_states: Dict[str, Any]) -> List[Dict]:
        """Prepare environment for predicted activity"""
        decisions = []
        
        device_id = prediction['action']['device_id']
        action_type = prediction['action']['action_type']
        
        # Pre-warm/prepare devices
        if action_type == 'device_control' and device_id.startswith('light_'):
            # Pre-dim lights for expected usage
            current_device = current_states.get(device_id, {})
            if not current_device.get('on', False):
                decisions.append({
                    'type': 'predictive_preparation',
                    'device_id': device_id,
                    'action': {'on': True, 'brightness': 50},
                    'reason': f'Predictive lighting for anticipated usage in {prediction["time_until"]} minutes',
                    'confidence': prediction['confidence']
                })
        
        return decisions

    def _get_learned_bedtime(self) -> Optional[int]:
        """Get the user's typical bedtime hour"""
        patterns = db_handler.get_user_behavior_patterns()
        
        # Look for patterns of turning off lights or setting sleep scenes
        bedtime_hours = []
        for pattern in patterns:
            if (pattern['action_type'] == 'scene_application' and 
                'sleep' in pattern['action_data'].get('scene_name', '').lower()):
                bedtime_hours.append(pattern['time_of_day'])
            elif (pattern['device_id'].startswith('light_') and 
                  pattern['action_data'].get('on') == False and 
                  pattern['time_of_day'] >= 20):
                bedtime_hours.append(pattern['time_of_day'])
        
        if bedtime_hours:
            return int(statistics.median(bedtime_hours))
        return None

    def _get_learned_wake_time(self) -> Optional[int]:
        """Get the user's typical wake time"""
        patterns = db_handler.get_user_behavior_patterns()
        
        wake_hours = []
        for pattern in patterns:
            if (pattern['action_type'] == 'scene_application' and 
                'morning' in pattern['action_data'].get('scene_name', '').lower()):
                wake_hours.append(pattern['time_of_day'])
            elif (pattern['device_id'].startswith('light_') and 
                  pattern['action_data'].get('on') == True and 
                  pattern['time_of_day'] <= 10):
                wake_hours.append(pattern['time_of_day'])
        
        if wake_hours:
            return int(statistics.median(wake_hours))
        return None

    def _minutes_until_bedtime(self, bedtime_hour: int, current_time: datetime) -> int:
        """Calculate minutes until bedtime"""
        bedtime_today = current_time.replace(hour=bedtime_hour, minute=0, second=0, microsecond=0)
        if bedtime_today <= current_time:
            bedtime_today += timedelta(days=1)
        
        delta = bedtime_today - current_time
        return int(delta.total_seconds() / 60)

    def _minutes_until_wake(self, wake_hour: int, current_time: datetime) -> int:
        """Calculate minutes until wake time"""
        wake_today = current_time.replace(hour=wake_hour, minute=0, second=0, microsecond=0)
        if wake_today <= current_time:
            wake_today += timedelta(days=1)
        
        delta = wake_today - current_time
        return int(delta.total_seconds() / 60)

    def _pre_sleep_preparation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Prepare environment for sleep"""
        decisions = []
        
        # Gradually dim lights
        for device_id, device in current_states.items():
            if device.get('type') == 'light' and device.get('on', False):
                current_brightness = device.get('brightness', 70)
                if current_brightness > 30:
                    decisions.append({
                        'type': 'pre_sleep_preparation',
                        'device_id': device_id,
                        'action': {'brightness': max(30, current_brightness - 20), 'color': '#FF6B35'},
                        'reason': 'Pre-sleep preparation - dimming lights'
                    })
        
        return decisions

    def _bedtime_optimization(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Optimize environment for bedtime"""
        decisions = []
        
        # Set sleep-optimal temperature
        ac_device = current_states.get('ac_main', {})
        if ac_device.get('on', False) and ac_device.get('temperature', 24) > 22:
            decisions.append({
                'type': 'bedtime_optimization',
                'device_id': 'ac_main',
                'action': {'temperature': 22},
                'reason': 'Bedtime optimization - sleep temperature'
            })
        
        return decisions

    def _is_sleep_hours(self, current_time: datetime) -> bool:
        """Check if current time is during typical sleep hours"""
        hour = current_time.hour
        return hour >= 23 or hour <= 6

    def _sleep_quality_optimization(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Optimize environment during sleep hours"""
        decisions = []
        
        # Ensure all lights are off except bedroom night light
        for device_id, device in current_states.items():
            if (device.get('type') == 'light' and device.get('on', False) and 
                device_id != 'light_bedroom'):
                decisions.append({
                    'type': 'sleep_quality_optimization',
                    'device_id': device_id,
                    'action': {'on': False},
                    'reason': 'Sleep quality - ensuring dark environment'
                })
            elif device_id == 'light_bedroom' and device.get('brightness', 0) > 10:
                decisions.append({
                    'type': 'sleep_quality_optimization',
                    'device_id': device_id,
                    'action': {'brightness': 5, 'color': '#8B0000'},
                    'reason': 'Sleep quality - minimal night lighting'
                })
        
        return decisions

    def _wake_up_preparation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Prepare environment for waking up"""
        decisions = []
        
        # Gradually increase bedroom lighting
        bedroom_light = current_states.get('light_bedroom', {})
        if not bedroom_light.get('on', False) or bedroom_light.get('brightness', 0) < 50:
            decisions.append({
                'type': 'wake_up_preparation',
                'device_id': 'light_bedroom',
                'action': {'on': True, 'brightness': 40, 'color': '#FFFACD'},
                'reason': 'Wake-up preparation - gentle morning lighting'
            })
        
        return decisions

    def _detect_unusual_activity(self, current_time: datetime) -> bool:
        """Detect if current activity is unusual"""
        # Simplified: check if someone is active during unusual hours
        hour = current_time.hour
        return 2 <= hour <= 5  # Unusual activity between 2-5 AM

    def _unusual_activity_response(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Respond to unusual activity"""
        decisions = []
        
        # Gentle lighting for safety
        decisions.append({
            'type': 'unusual_activity_response',
            'device_id': 'light_living_room',
            'action': {'on': True, 'brightness': 30, 'color': '#4B0082'},
            'reason': 'Unusual activity detected - providing safe lighting'
        })
        
        return decisions

    def _is_guest_detected(self, face_recognition_data: Dict[str, Any]) -> bool:
        """Check if guests are detected"""
        # In a real system, this would analyze face recognition data
        return False  # Simplified for now

    def _guest_mode_activation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Activate guest-friendly automation"""
        decisions = []
        
        # Brighter, more welcoming lighting
        decisions.append({
            'type': 'guest_mode_activation',
            'device_id': 'light_living_room',
            'action': {'on': True, 'brightness': 80, 'color': '#F0F8FF'},
            'reason': 'Guest detected - welcoming lighting'
        })
        
        return decisions

    def _should_auto_arm_security(self, current_time: datetime) -> bool:
        """Determine if security should be automatically armed"""
        # Auto-arm during typical sleep hours
        hour = current_time.hour
        return hour >= 23 or hour <= 6

    def _auto_security_activation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Automatically activate security system"""
        decisions = []
        
        security_device = current_states.get('security_system', {})
        if not security_device.get('armed', False):
            decisions.append({
                'type': 'auto_security_activation',
                'device_id': 'security_system',
                'action': {'armed': True, 'mode': 'night'},
                'reason': 'Auto-arming security for night hours'
            })
        
        return decisions

    def _detect_vacation_mode(self) -> bool:
        """Detect if users are on vacation"""
        # Simplified: would check for extended absence patterns
        return False

    def _vacation_mode_automation(self, current_states: Dict[str, Any]) -> List[Dict]:
        """Automation for vacation mode"""
        decisions = []
        
        # Random lighting to simulate presence
        decisions.append({
            'type': 'vacation_mode',
            'device_id': 'light_living_room',
            'action': {'on': True, 'brightness': 60},
            'reason': 'Vacation mode - simulating presence'
        })
        
        return decisions

    def _get_mood_weather_optimization(self, current_mood: str, 
                                     weather_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Get optimal settings based on mood and weather"""
        # Mood-weather matrix for optimal settings
        optimizations = {}
        
        if current_mood == 'Energetic' and weather_data.get('condition') == 'Rain':
            # Compensate for gloomy weather with bright energetic lighting
            optimizations['light_living_room'] = {'brightness': 90, 'color': '#00FF7F'}
            optimizations['light_kitchen'] = {'brightness': 85, 'color': '#FFFFFF'}
        
        elif current_mood == 'Relax' and weather_data.get('temperature', 25) > 28:
            # Hot weather + relax mood = cooler, calmer environment
            optimizations['ac_main'] = {'temperature': 21, 'on': True}
            optimizations['light_living_room'] = {'brightness': 40, 'color': '#87CEEB'}
        
        return optimizations

    def _suggest_mood_for_weather(self, weather_data: Dict[str, Any]) -> Optional[str]:
        """Suggest optimal mood based on weather"""
        condition = weather_data.get('condition', '').lower()
        temperature = weather_data.get('temperature', 25)
        
        if 'rain' in condition or 'storm' in condition:
            return 'Relax'  # Cozy mood for rainy weather
        elif 'clear' in condition and 15 <= temperature <= 25:
            return 'Energetic'  # Perfect weather for energy
        elif temperature > 28:
            return 'Relax'  # Too hot for high energy
        
        return None

    def _settings_need_adjustment(self, current_device: Dict[str, Any], 
                                optimal_settings: Dict[str, Any]) -> bool:
        """Check if device settings need adjustment"""
        for key, value in optimal_settings.items():
            if current_device.get(key) != value:
                return True
        return False

    def _weekend_predictions(self, current_states: Dict[str, Any], 
                           current_time: datetime) -> List[Dict]:
        """Weekend-specific predictions"""
        decisions = []
        
        # Weekend morning routine (later wake-up)
        if 9 <= current_time.hour <= 11:
            decisions.append({
                'type': 'weekend_prediction',
                'device_id': 'light_living_room',
                'action': {'on': True, 'brightness': 70},
                'reason': 'Weekend morning routine - leisurely lighting'
            })
        
        return decisions

    def _weekday_predictions(self, current_states: Dict[str, Any], 
                           current_time: datetime) -> List[Dict]:
        """Weekday-specific predictions"""
        decisions = []
        
        # Weekday morning routine (earlier, more energetic)
        if 6 <= current_time.hour <= 8:
            decisions.append({
                'type': 'weekday_prediction',
                'device_id': 'light_kitchen',
                'action': {'on': True, 'brightness': 85},
                'reason': 'Weekday morning routine - energetic lighting'
            })
        
        return decisions

    def get_automation_insights(self) -> Dict[str, Any]:
        """Get insights about advanced automation features"""
        return {
            'energy_optimization_active': self.energy_savings_enabled,
            'occupancy_detection_active': self.occupancy_simulation,
            'predictive_scheduling_active': self.predictive_mode,
            'sleep_optimization_active': self.sleep_optimization,
            'security_intelligence_active': self.security_intelligence,
            'features_count': 5
        }

# Global advanced automation instance
advanced_automation = AdvancedAutomation() 