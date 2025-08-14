import os
import sys
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, Tuple, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.device_simulator import device_simulator
from core.mood_engine import mood_engine
from core.proactive_engine import proactive_engine

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables")

def parse_device_commands(user_message: str) -> List[Dict[str, Any]]:
    """
    Parse user message to extract device commands
    
    Returns:
        List of device commands to execute
    """
    commands = []
    message_lower = user_message.lower()
    
    # Get current device states
    devices = device_simulator.get_all_device_states()
    
    # Light commands
    if any(word in message_lower for word in ['light', 'lights', 'lamp', 'lamps']):
        if 'turn on' in message_lower or 'switch on' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'light':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'on': True},
                        'action': f"Turned on {device['name']}"
                    })
        elif 'turn off' in message_lower or 'switch off' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'light':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'on': False},
                        'action': f"Turned off {device['name']}"
                    })
        elif 'dim' in message_lower or 'brightness' in message_lower:
            # Extract brightness percentage if mentioned
            brightness_match = re.search(r'(\d+)%?', message_lower)
            brightness = int(brightness_match.group(1)) if brightness_match else 30
            for device_id, device in devices.items():
                if device.get('type') == 'light':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'on': True, 'brightness': brightness},
                        'action': f"Set {device['name']} brightness to {brightness}%"
                    })
    
    # AC/Temperature commands
    if any(word in message_lower for word in ['temperature', 'ac', 'air conditioning', 'thermostat']):
        temp_match = re.search(r'(\d+)\s*(?:degrees?|°)', message_lower)
        if temp_match:
            temperature = int(temp_match.group(1))
            for device_id, device in devices.items():
                if device.get('type') == 'ac':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'on': True, 'temperature': temperature},
                        'action': f"Set {device['name']} to {temperature}°C"
                    })
        elif 'turn on' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'ac':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'on': True},
                        'action': f"Turned on {device['name']}"
                    })
        elif 'turn off' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'ac':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'on': False},
                        'action': f"Turned off {device['name']}"
                    })
    
    # Music commands
    if any(word in message_lower for word in ['music', 'song', 'play', 'pause', 'volume']):
        if 'play' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'music':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'playing': True},
                        'action': f"Started playing music on {device['name']}"
                    })
        elif 'pause' in message_lower or 'stop' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'music':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'playing': False},
                        'action': f"Paused music on {device['name']}"
                    })
        elif 'volume' in message_lower:
            volume_match = re.search(r'(\d+)%?', message_lower)
            if volume_match:
                volume = int(volume_match.group(1))
                for device_id, device in devices.items():
                    if device.get('type') == 'music':
                        commands.append({
                            'device_id': device_id,
                            'updates': {'volume': volume},
                            'action': f"Set {device['name']} volume to {volume}%"
                        })
    
    # Door commands
    if any(word in message_lower for word in ['door', 'lock', 'unlock']):
        if 'lock' in message_lower and 'unlock' not in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'door':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'locked': True},
                        'action': f"Locked {device['name']}"
                    })
        elif 'unlock' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'door':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'locked': False},
                        'action': f"Unlocked {device['name']}"
                    })
    
    # Blinds commands
    if any(word in message_lower for word in ['blinds', 'curtains', 'shades']):
        if 'open' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'blinds':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'open': True, 'position': 100},
                        'action': f"Opened {device['name']}"
                    })
        elif 'close' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'blinds':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'open': False, 'position': 0},
                        'action': f"Closed {device['name']}"
                    })
    
    # Security commands
    if any(word in message_lower for word in ['security', 'alarm', 'arm', 'disarm']):
        if 'arm' in message_lower and 'disarm' not in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'security':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'armed': True, 'mode': 'home'},
                        'action': f"Armed {device['name']}"
                    })
        elif 'disarm' in message_lower:
            for device_id, device in devices.items():
                if device.get('type') == 'security':
                    commands.append({
                        'device_id': device_id,
                        'updates': {'armed': False, 'mode': 'off'},
                        'action': f"Disarmed {device['name']}"
                    })
    
    return commands

def parse_scene_commands(user_message: str) -> str:
    """
    Parse user message to extract scene commands
    
    Returns:
        Scene name if found, None otherwise
    """
    message_lower = user_message.lower()
    
    scene_keywords = {
        'movie': 'Movie Mode',
        'cinema': 'Movie Mode',
        'film': 'Movie Mode',
        'morning': 'Good Morning',
        'wake up': 'Good Morning',
        'relax': 'Relax',
        'chill': 'Relax',
        'calm': 'Relax',
        'energetic': 'Energetic',
        'energy': 'Energetic',
        'bright': 'Energetic',
        'focus': 'Focus',
        'work': 'Focus',
        'concentrate': 'Focus',
        'sleep': 'Sleep',
        'bedtime': 'Sleep',
        'night': 'Sleep'
    }
    
    for keyword, scene in scene_keywords.items():
        if keyword in message_lower:
            return scene
    
    return None

def parse_mood_commands(user_message: str) -> str:
    """
    Parse user message to extract mood commands
    
    Returns:
        Mood name if found, None otherwise
    """
    message_lower = user_message.lower()
    
    available_moods = mood_engine.get_available_moods()
    
    for mood in available_moods:
        if mood.lower() in message_lower:
            return mood
    
    return None

async def get_gemini_response(user_message: str) -> Tuple[str, Dict[str, Any]]:
    """
    Get response from Gemini LLM and execute device commands if found
    
    Args:
        user_message (str): The user's input message
        
    Returns:
        Tuple[str, Dict[str, Any]]: (AI response, device changes)
        
    Raises:
        Exception: If API key is missing or API call fails
    """
    device_changes = {
        'devices_updated': {},
        'scene_applied': None,
        'mood_changed': None
    }
    
    try:
        # Parse and execute device commands
        device_commands = parse_device_commands(user_message)
        executed_actions = []
        
        for command in device_commands:
            try:
                updated_state = device_simulator.update_device_state(
                    command['device_id'], 
                    command['updates']
                )
                device_changes['devices_updated'][command['device_id']] = updated_state
                executed_actions.append(command['action'])
                
                # Log user behavior for learning
                proactive_engine.log_user_action(
                    user_id="user_via_chat",  # Default user ID for chat interactions
                    device_id=command['device_id'],
                    action_type="device_control",
                    action_data=command['updates']
                )
            except Exception as e:
                print(f"Error executing device command: {e}")
        
        # Parse and execute scene commands
        scene_name = parse_scene_commands(user_message)
        if scene_name:
            try:
                updated_devices = device_simulator.apply_scene(scene_name)
                device_changes['devices_updated'].update(updated_devices)
                device_changes['scene_applied'] = scene_name
                executed_actions.append(f"Applied {scene_name} scene")
                
                # Log scene application for learning
                proactive_engine.log_user_action(
                    user_id="user_via_chat",
                    device_id="scene_controller",
                    action_type="scene_application",
                    action_data={"scene_name": scene_name}
                )
            except Exception as e:
                print(f"Error applying scene: {e}")
        
        # Parse and execute mood commands
        mood_name = parse_mood_commands(user_message)
        if mood_name:
            try:
                theme_vars, updated_devices = mood_engine.set_mood(mood_name)
                device_changes['devices_updated'].update(updated_devices)
                device_changes['mood_changed'] = {
                    'mood_name': mood_name,
                    'theme_vars': theme_vars
                }
                executed_actions.append(f"Changed mood to {mood_name}")
            except Exception as e:
                print(f"Error changing mood: {e}")
        
        # Generate AI response
        if not GEMINI_API_KEY:
            ai_response = "Sorry, I'm not properly configured. Please check the GEMINI_API_KEY environment variable."
        else:
            # Initialize the Gemini model
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Create a system prompt that acknowledges actual device control
            if executed_actions:
                action_summary = "I have successfully executed the following actions: " + ", ".join(executed_actions) + ". "
            else:
                action_summary = ""
            
            system_prompt = f"""You are Genie, an AI-powered smart home assistant. You help users control their smart home devices through natural language commands.

{action_summary}

You can control:
- Lights (turn on/off, dim, change colors)
- Air conditioning (temperature, fan speed, mode)
- Music systems (play, pause, volume, change songs)
- Security systems
- Blinds and curtains
- Door locks
- And other smart home devices

Respond in a friendly, helpful manner. When users ask you to control devices, acknowledge what you've done and provide a brief, natural response. Be conversational and avoid being too technical.

User message: """
            
            # Combine system prompt with user message
            full_prompt = system_prompt + user_message
            
            # Generate response
            try:
                response = model.generate_content(full_prompt)
                if response.text:
                    ai_response = response.text
                else:
                    ai_response = "I'm sorry, I couldn't generate a response. Please try again."
            except Exception as e:
                print(f"Error generating AI response: {e}")
                if executed_actions:
                    ai_response = f"I've {', '.join(executed_actions).lower()}. How else can I help you?"
                else:
                    ai_response = "I'm experiencing some technical difficulties with my AI response, but I'm still here to help!"
        
        return ai_response, device_changes
            
    except Exception as e:
        print(f"Error in get_gemini_response: {str(e)}")
        error_response = f"I'm experiencing some technical difficulties: {str(e)}"
        return error_response, device_changes 