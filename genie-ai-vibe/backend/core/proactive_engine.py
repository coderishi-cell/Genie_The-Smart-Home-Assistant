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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db_handler
from core.device_simulator import device_simulator
from core.weather_service import weather_service
from core.advanced_automation import advanced_automation
from core.smart_mood_integration import smart_mood_integration
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ProactiveEngine:
    def __init__(self):
        self.is_running = False
        self.automation_thread = None
        self.check_interval = 300  # Check every 5 minutes
        self.last_weather_check = None
        self.last_time_check = None
        self.user_patterns = {}
        self.face_recognition_data = {}  # To store recognized users
        
        # Initialize database
        db_handler.init_db()
        
        print("🧠 Proactive Engine initialized - Ready to learn and adapt!")

    def start_proactive_automation(self):
        """Start the proactive automation system"""
        if self.is_running:
            print("⚠️ Proactive automation is already running")
            return
        
        self.is_running = True
        self.automation_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.automation_thread.start()
        print("🚀 Proactive automation started - Genie is now learning and adapting!")

    def stop_proactive_automation(self):
        """Stop the proactive automation system"""
        self.is_running = False
        if self.automation_thread:
            self.automation_thread.join(timeout=5)
        print("⏹️ Proactive automation stopped")

    def _automation_loop(self):
        """Main automation loop that runs continuously"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Run different checks based on intervals
                asyncio.run(self._check_time_based_automation(current_time))
                asyncio.run(self._check_weather_based_automation(current_time))
                asyncio.run(self._check_pattern_based_automation(current_time))
                asyncio.run(self._check_advanced_automation(current_time))
                self._update_user_patterns()
                
                # Sleep for the check interval
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Error in automation loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    async def _check_time_based_automation(self, current_time: datetime):
        """Check for time-based automation opportunities"""
        try:
            hour = current_time.hour
            minute = current_time.minute
            day_of_week = current_time.weekday()
            
            # Skip if we've already checked this hour
            if self.last_time_check and self.last_time_check.hour == hour:
                return
            
            self.last_time_check = current_time
            
            # Get current device states
            current_states = device_simulator.get_all_device_states()
            
            # Get user behavior patterns for this time
            patterns = db_handler.get_user_behavior_patterns(
                time_of_day=hour, 
                day_of_week=day_of_week
            )
            
            # Analyze patterns and make decisions
            decisions = self._analyze_time_patterns(patterns, current_states, hour, day_of_week)
            
            for decision in decisions:
                await self._execute_proactive_decision(decision)
                
        except Exception as e:
            print(f"❌ Error in time-based automation: {e}")

    async def _check_weather_based_automation(self, current_time: datetime):
        """Check for weather-based automation opportunities"""
        try:
            # Check weather every 30 minutes
            if (self.last_weather_check and 
                current_time - self.last_weather_check < timedelta(minutes=30)):
                return
            
            self.last_weather_check = current_time
            
            # Get current weather
            weather_data = weather_service.get_current_weather()
            if not weather_data:
                return
            
            # Get comfort recommendations
            comfort_recs = weather_service.get_comfort_recommendations(weather_data)
            
            # Get current device states
            current_states = device_simulator.get_all_device_states()
            
            # Make weather-based decisions
            decisions = self._analyze_weather_automation(weather_data, comfort_recs, current_states)
            
            for decision in decisions:
                await self._execute_proactive_decision(decision)
                
        except Exception as e:
            print(f"❌ Error in weather-based automation: {e}")

    async def _check_pattern_based_automation(self, current_time: datetime):
        """Check for pattern-based automation based on learned behavior"""
        try:
            # Get recent user behavior patterns
            recent_patterns = db_handler.get_user_behavior_patterns()
            
            if not recent_patterns:
                return
            
            # Analyze patterns for predictive actions
            predictions = self._predict_user_needs(recent_patterns, current_time)
            
            for prediction in predictions:
                await self._execute_proactive_decision(prediction)
                
        except Exception as e:
            print(f"❌ Error in pattern-based automation: {e}")

    async def _check_advanced_automation(self, current_time: datetime):
        """Check for advanced automation opportunities"""
        try:
            current_states = device_simulator.get_all_device_states()
            weather_data = weather_service.get_current_weather()
            
            # Run all advanced automation checks
            energy_decisions = await advanced_automation.energy_optimization_automation(current_states)
            occupancy_decisions = await advanced_automation.occupancy_based_automation()
            predictive_decisions = await advanced_automation.predictive_scheduling_automation()
            sleep_decisions = await advanced_automation.sleep_optimization_automation(current_states)
            security_decisions = await advanced_automation.security_intelligence_automation(current_states)
            
            # Smart mood suggestions
            mood_suggestion = await smart_mood_integration.suggest_optimal_mood({'current_time': current_time})
            mood_decisions = []
            if mood_suggestion and mood_suggestion.get('confidence', 0) > 0.8:
                # High confidence mood suggestion - apply it
                suggested_mood = mood_suggestion['suggested_mood']
                mood_automations = await smart_mood_integration.mood_based_automation(suggested_mood)
                mood_decisions.extend(mood_automations)
            
            # Combine all decisions
            all_decisions = (energy_decisions + occupancy_decisions + predictive_decisions + 
                           sleep_decisions + security_decisions + mood_decisions)
            
            # Execute each decision
            for decision in all_decisions:
                await self._execute_proactive_decision(decision)
                
        except Exception as e:
            print(f"❌ Error in advanced automation: {e}")

    def _analyze_time_patterns(self, patterns: List[Dict], current_states: Dict, 
                              hour: int, day_of_week: int) -> List[Dict]:
        """Analyze time-based patterns and suggest actions"""
        decisions = []
        
        # Group patterns by device
        device_patterns = defaultdict(list)
        for pattern in patterns:
            device_patterns[pattern['device_id']].append(pattern)
        
        # Morning routine (6-10 AM)
        if 6 <= hour <= 10:
            decisions.extend(self._suggest_morning_routine(current_states, patterns))
        
        # Evening routine (6-10 PM)
        elif 18 <= hour <= 22:
            decisions.extend(self._suggest_evening_routine(current_states, patterns))
        
        # Night routine (10 PM - 2 AM)
        elif hour >= 22 or hour <= 2:
            decisions.extend(self._suggest_night_routine(current_states, patterns))
        
        return decisions

    def _analyze_weather_automation(self, weather_data: Dict, comfort_recs: Dict, 
                                   current_states: Dict) -> List[Dict]:
        """Analyze weather conditions and suggest automations"""
        decisions = []
        
        # AC temperature adjustment
        recommended_temp = comfort_recs.get('ac_temp', 24)
        ac_device = current_states.get('ac_main', {})
        
        if ac_device and abs(ac_device.get('temperature', 24) - recommended_temp) > 2:
            decisions.append({
                'type': 'weather_ac_adjustment',
                'device_id': 'ac_main',
                'action': {'temperature': recommended_temp, 'on': True},
                'reason': f"Weather-based temperature adjustment to {recommended_temp}°C",
                'weather_context': weather_data,
                'comfort_recs': comfort_recs
            })
        
        # Lighting adjustment based on weather
        lighting_rec = comfort_recs.get('lighting', 'normal')
        if lighting_rec == 'bright':
            for device_id, device in current_states.items():
                if device.get('type') == 'light' and device.get('brightness', 0) < 80:
                    decisions.append({
                        'type': 'weather_lighting_adjustment',
                        'device_id': device_id,
                        'action': {'brightness': 85, 'on': True},
                        'reason': f"Increased lighting due to {weather_data.get('condition', 'weather')}",
                        'weather_context': weather_data
                    })
        
        return decisions

    def _suggest_morning_routine(self, current_states: Dict, patterns: List[Dict]) -> List[Dict]:
        """Suggest morning routine automations"""
        decisions = []
        
        # Typical morning actions
        morning_actions = [
            {'device_id': 'light_living_room', 'action': {'on': True, 'brightness': 80}, 
             'reason': 'Morning routine - brighten living room'},
            {'device_id': 'light_kitchen', 'action': {'on': True, 'brightness': 85}, 
             'reason': 'Morning routine - kitchen lighting'},
            {'device_id': 'blinds_living_room', 'action': {'open': True, 'position': 100}, 
             'reason': 'Morning routine - open blinds for natural light'}
        ]
        
        # Only suggest if devices are currently off/closed
        for action in morning_actions:
            device_id = action['device_id']
            device = current_states.get(device_id, {})
            
            if device_id in current_states:
                if (device.get('type') == 'light' and not device.get('on', False)) or \
                   (device.get('type') == 'blinds' and not device.get('open', False)):
                    decisions.append({
                        'type': 'morning_routine',
                        'device_id': device_id,
                        'action': action['action'],
                        'reason': action['reason']
                    })
        
        return decisions

    def _suggest_evening_routine(self, current_states: Dict, patterns: List[Dict]) -> List[Dict]:
        """Suggest evening routine automations"""
        decisions = []
        
        # Typical evening actions
        evening_actions = [
            {'device_id': 'light_living_room', 'action': {'on': True, 'brightness': 60, 'color': '#FFD700'}, 
             'reason': 'Evening routine - warm living room lighting'},
            {'device_id': 'security_system', 'action': {'armed': True, 'mode': 'night'}, 
             'reason': 'Evening routine - enable security'}
        ]
        
        for action in evening_actions:
            device_id = action['device_id']
            if device_id in current_states:
                decisions.append({
                    'type': 'evening_routine',
                    'device_id': device_id,
                    'action': action['action'],
                    'reason': action['reason']
                })
        
        return decisions

    def _suggest_night_routine(self, current_states: Dict, patterns: List[Dict]) -> List[Dict]:
        """Suggest night routine automations"""
        decisions = []
        
        # Typical night actions
        night_actions = [
            {'device_id': 'light_living_room', 'action': {'on': False}, 
             'reason': 'Night routine - turn off living room lights'},
            {'device_id': 'light_kitchen', 'action': {'on': False}, 
             'reason': 'Night routine - turn off kitchen lights'},
            {'device_id': 'door_front', 'action': {'locked': True}, 
             'reason': 'Night routine - secure front door'},
            {'device_id': 'ac_main', 'action': {'temperature': 22}, 
             'reason': 'Night routine - cooler temperature for sleep'}
        ]
        
        for action in night_actions:
            device_id = action['device_id']
            if device_id in current_states:
                decisions.append({
                    'type': 'night_routine',
                    'device_id': device_id,
                    'action': action['action'],
                    'reason': action['reason']
                })
        
        return decisions

    def _predict_user_needs(self, patterns: List[Dict], current_time: datetime) -> List[Dict]:
        """Predict user needs based on historical patterns"""
        predictions = []
        
        # Group patterns by time and device
        time_patterns = defaultdict(list)
        for pattern in patterns:
            key = f"{pattern['time_of_day']}_{pattern['device_id']}"
            time_patterns[key].append(pattern)
        
        # Look for patterns that happen regularly at this time
        current_hour = current_time.hour
        for key, pattern_list in time_patterns.items():
            if len(pattern_list) >= 3:  # At least 3 occurrences
                time_hour, device_id = key.split('_', 1)
                if int(time_hour) == current_hour:
                    # Predict this action might be needed
                    most_common_action = self._get_most_common_action(pattern_list)
                    if most_common_action:
                        predictions.append({
                            'type': 'pattern_prediction',
                            'device_id': device_id,
                            'action': most_common_action,
                            'reason': f'Learned pattern: User usually controls {device_id} at {current_hour}:00',
                            'confidence': min(len(pattern_list) / 10, 1.0)
                        })
        
        return predictions

    def _get_most_common_action(self, patterns: List[Dict]) -> Optional[Dict]:
        """Get the most common action from patterns"""
        action_counts = defaultdict(int)
        
        for pattern in patterns:
            action_key = json.dumps(pattern['action_data'], sort_keys=True)
            action_counts[action_key] += 1
        
        if action_counts:
            most_common = max(action_counts.items(), key=lambda x: x[1])
            return json.loads(most_common[0])
        
        return None

    async def _execute_proactive_decision(self, decision: Dict):
        """Execute a proactive decision using LLM reasoning"""
        try:
            # Get current device states
            current_states = device_simulator.get_all_device_states()
            
            # Get current weather for context
            weather_data = weather_service.get_current_weather()
            
            # Use LLM to validate and enhance the decision
            llm_decision = await self._get_llm_decision(decision, current_states, weather_data)
            
            if llm_decision['should_execute']:
                # Execute the action
                device_id = decision['device_id']
                action = decision['action']
                
                # Update device state
                updated_state = device_simulator.update_device_state(device_id, action)
                
                # Log the automation decision
                db_handler.log_automation_decision(
                    decision_type=decision['type'],
                    trigger_reason=decision['reason'],
                    action_taken=f"Updated {device_id}: {action}",
                    device_states_before={device_id: current_states.get(device_id, {})},
                    device_states_after={device_id: updated_state},
                    weather_data=weather_data,
                    llm_reasoning=llm_decision['reasoning']
                )
                
                print(f"🤖 Proactive action executed: {decision['reason']}")
                print(f"   Device: {device_id}, Action: {action}")
                print(f"   LLM reasoning: {llm_decision['reasoning']}")
            else:
                print(f"🚫 Proactive action rejected by LLM: {llm_decision['reasoning']}")
                
        except Exception as e:
            print(f"❌ Error executing proactive decision: {e}")

    async def _get_llm_decision(self, decision: Dict, current_states: Dict, 
                               weather_data: Dict) -> Dict[str, Any]:
        """Use LLM to validate and enhance automation decisions"""
        try:
            if not GEMINI_API_KEY:
                return {
                    'should_execute': True,
                    'reasoning': 'LLM validation disabled - no API key'
                }
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Create context for the LLM
            context = {
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day_of_week': datetime.now().strftime('%A'),
                'proposed_action': decision,
                'current_device_states': current_states,
                'weather': weather_data,
                'device_being_changed': current_states.get(decision['device_id'], {})
            }
            
            prompt = f"""
You are Genie, an AI smart home assistant making proactive decisions. 

CONTEXT:
- Current time: {context['current_time']} ({context['day_of_week']})
- Weather: {weather_data.get('condition', 'Unknown')} at {weather_data.get('temperature', 'Unknown')}°C
- Proposed action: {decision['reason']}
- Device to change: {decision['device_id']}
- Current device state: {context['device_being_changed']}
- Proposed changes: {decision['action']}

GUIDELINES:
- Only approve actions that make sense for the current context
- Consider user comfort, energy efficiency, and safety
- Avoid unnecessary changes (e.g., don't turn on lights that are already on)
- Be conservative with temperature changes (max 3°C adjustment)
- Consider the time of day and weather conditions
- Reject actions that might disturb sleeping users late at night

Should I execute this proactive action? Respond with JSON format:
{{"should_execute": true/false, "reasoning": "explanation of your decision"}}
"""
            
            response = model.generate_content(prompt)
            
            if response.text:
                # Try to parse JSON response
                try:
                    result = json.loads(response.text.strip())
                    return {
                        'should_execute': result.get('should_execute', False),
                        'reasoning': result.get('reasoning', 'No reasoning provided')
                    }
                except json.JSONDecodeError:
                    # Fallback parsing
                    text = response.text.lower()
                    should_execute = 'true' in text and 'should_execute' in text
                    return {
                        'should_execute': should_execute,
                        'reasoning': response.text[:200]
                    }
            else:
                return {
                    'should_execute': False,
                    'reasoning': 'LLM did not provide a response'
                }
                
        except Exception as e:
            print(f"❌ Error in LLM decision: {e}")
            return {
                'should_execute': False,
                'reasoning': f'LLM error: {str(e)}'
            }

    def _update_user_patterns(self):
        """Update user patterns cache"""
        try:
            patterns = db_handler.get_user_behavior_patterns()
            self.user_patterns = {}
            
            for pattern in patterns:
                key = f"{pattern['time_of_day']}_{pattern['day_of_week']}_{pattern['device_id']}"
                if key not in self.user_patterns:
                    self.user_patterns[key] = []
                self.user_patterns[key].append(pattern)
                
        except Exception as e:
            print(f"❌ Error updating user patterns: {e}")

    def log_user_action(self, user_id: str, device_id: str, action_type: str, 
                       action_data: Dict[str, Any]):
        """Log a user action for learning"""
        try:
            # Get current weather for context
            weather_data = weather_service.get_current_weather()
            weather_condition = weather_data.get('condition') if weather_data else None
            temperature = weather_data.get('temperature') if weather_data else None
            
            # Log the behavior
            db_handler.log_user_behavior(
                user_id=user_id,
                device_id=device_id,
                action_type=action_type,
                action_data=action_data,
                weather_condition=weather_condition,
                temperature=temperature
            )
            
            print(f"📊 Logged user behavior: {user_id} -> {device_id} ({action_type})")
            
        except Exception as e:
            print(f"❌ Error logging user action: {e}")

    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status and statistics"""
        try:
            # Get recent automation decisions
            recent_decisions = db_handler.get_automation_history(limit=10)
            
            # Get user patterns count
            patterns = db_handler.get_user_behavior_patterns()
            
            # Get user preferences
            preferences = db_handler.get_user_preferences()
            
            return {
                'is_running': self.is_running,
                'check_interval_minutes': self.check_interval // 60,
                'recent_decisions': recent_decisions,
                'total_learned_patterns': len(patterns),
                'total_preferences': len(preferences),
                'last_weather_check': self.last_weather_check.isoformat() if self.last_weather_check else None,
                'last_time_check': self.last_time_check.isoformat() if self.last_time_check else None
            }
            
        except Exception as e:
            print(f"❌ Error getting automation status: {e}")
            return {'is_running': self.is_running, 'error': str(e)}

# Global proactive engine instance
proactive_engine = ProactiveEngine() 