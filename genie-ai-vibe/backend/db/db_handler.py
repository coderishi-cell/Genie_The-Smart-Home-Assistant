import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Database file path
DB_PATH = "./genie.db"

def init_db():
    """Initialize the SQLite database and create tables if they don't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create device_states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_states (
                device_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create mood_settings table for future use
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mood_settings (
                mood_name TEXT PRIMARY KEY,
                settings_json TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create user_behavior_patterns table for learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                device_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT NOT NULL,
                time_of_day INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                weather_condition TEXT,
                temperature REAL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create automation_decisions table to track proactive actions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type TEXT NOT NULL,
                trigger_reason TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                device_states_before TEXT,
                device_states_after TEXT,
                weather_data TEXT,
                time_context TEXT NOT NULL,
                llm_reasoning TEXT,
                success BOOLEAN DEFAULT 1,
                user_feedback TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Create user_preferences table for learned preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT NOT NULL,
                context TEXT NOT NULL,
                preference_data TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 1,
                last_updated TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully with proactive intelligence tables")
        
    except Exception as e:
        print(f"Error initializing database: {e}")

def get_all_device_states() -> Dict[str, Dict[str, Any]]:
    """Retrieve all device states from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT device_id, state_json FROM device_states")
        rows = cursor.fetchall()
        
        device_states = {}
        for device_id, state_json in rows:
            try:
                device_states[device_id] = json.loads(state_json)
            except json.JSONDecodeError:
                print(f"Error parsing JSON for device {device_id}")
                continue
        
        conn.close()
        return device_states
        
    except Exception as e:
        print(f"Error retrieving device states: {e}")
        return {}

def upsert_device_state(device_id: str, state: Dict[str, Any]):
    """Insert or update a device state in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        state_json = json.dumps(state)
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO device_states (device_id, state_json, timestamp)
            VALUES (?, ?, ?)
        ''', (device_id, state_json, timestamp))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error upserting device state for {device_id}: {e}")

def get_device_state(device_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific device state from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT state_json FROM device_states WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
        
    except Exception as e:
        print(f"Error retrieving device state for {device_id}: {e}")
        return None

# New functions for proactive intelligence

def log_user_behavior(user_id: str, device_id: str, action_type: str, action_data: Dict[str, Any], 
                     weather_condition: str = None, temperature: float = None):
    """Log user behavior for learning patterns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        action_data_json = json.dumps(action_data)
        
        cursor.execute('''
            INSERT INTO user_behavior_patterns 
            (user_id, device_id, action_type, action_data, time_of_day, day_of_week, 
             weather_condition, temperature, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, device_id, action_type, action_data_json, now.hour, now.weekday(),
              weather_condition, temperature, now.isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error logging user behavior: {e}")

def get_user_behavior_patterns(user_id: str = None, device_id: str = None, 
                              time_of_day: int = None, day_of_week: int = None) -> List[Dict[str, Any]]:
    """Get user behavior patterns based on filters"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM user_behavior_patterns WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        if time_of_day is not None:
            query += " AND time_of_day = ?"
            params.append(time_of_day)
        if day_of_week is not None:
            query += " AND day_of_week = ?"
            params.append(day_of_week)
            
        query += " ORDER BY timestamp DESC LIMIT 100"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        patterns = []
        for row in rows:
            patterns.append({
                'id': row[0],
                'user_id': row[1],
                'device_id': row[2],
                'action_type': row[3],
                'action_data': json.loads(row[4]),
                'time_of_day': row[5],
                'day_of_week': row[6],
                'weather_condition': row[7],
                'temperature': row[8],
                'timestamp': row[9]
            })
        
        conn.close()
        return patterns
        
    except Exception as e:
        print(f"Error retrieving user behavior patterns: {e}")
        return []

def log_automation_decision(decision_type: str, trigger_reason: str, action_taken: str,
                          device_states_before: Dict[str, Any], device_states_after: Dict[str, Any],
                          weather_data: Dict[str, Any] = None, llm_reasoning: str = None):
    """Log proactive automation decisions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now()
        time_context = {
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'date': now.date().isoformat()
        }
        
        cursor.execute('''
            INSERT INTO automation_decisions 
            (decision_type, trigger_reason, action_taken, device_states_before, 
             device_states_after, weather_data, time_context, llm_reasoning, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (decision_type, trigger_reason, action_taken, 
              json.dumps(device_states_before), json.dumps(device_states_after),
              json.dumps(weather_data) if weather_data else None,
              json.dumps(time_context), llm_reasoning, now.isoformat()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error logging automation decision: {e}")

def get_automation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent automation decisions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM automation_decisions 
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        
        decisions = []
        for row in rows:
            decisions.append({
                'id': row[0],
                'decision_type': row[1],
                'trigger_reason': row[2],
                'action_taken': row[3],
                'device_states_before': json.loads(row[4]) if row[4] else {},
                'device_states_after': json.loads(row[5]) if row[5] else {},
                'weather_data': json.loads(row[6]) if row[6] else None,
                'time_context': json.loads(row[7]) if row[7] else {},
                'llm_reasoning': row[8],
                'success': bool(row[9]),
                'user_feedback': row[10],
                'timestamp': row[11]
            })
        
        conn.close()
        return decisions
        
    except Exception as e:
        print(f"Error retrieving automation history: {e}")
        return []

def update_user_preference(preference_type: str, context: str, preference_data: Dict[str, Any], 
                          confidence_score: float = 1.0):
    """Update or create user preference"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if preference exists
        cursor.execute('''
            SELECT id, usage_count FROM user_preferences 
            WHERE preference_type = ? AND context = ?
        ''', (preference_type, context))
        
        row = cursor.fetchone()
        now = datetime.now().isoformat()
        
        if row:
            # Update existing preference
            preference_id, usage_count = row
            cursor.execute('''
                UPDATE user_preferences 
                SET preference_data = ?, confidence_score = ?, 
                    usage_count = ?, last_updated = ?
                WHERE id = ?
            ''', (json.dumps(preference_data), confidence_score, 
                  usage_count + 1, now, preference_id))
        else:
            # Create new preference
            cursor.execute('''
                INSERT INTO user_preferences 
                (preference_type, context, preference_data, confidence_score, usage_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (preference_type, context, json.dumps(preference_data), 
                  confidence_score, 1, now))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error updating user preference: {e}")

def get_user_preferences(preference_type: str = None) -> List[Dict[str, Any]]:
    """Get user preferences"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if preference_type:
            cursor.execute('''
                SELECT * FROM user_preferences 
                WHERE preference_type = ? 
                ORDER BY confidence_score DESC, usage_count DESC
            ''', (preference_type,))
        else:
            cursor.execute('''
                SELECT * FROM user_preferences 
                ORDER BY confidence_score DESC, usage_count DESC
            ''')
        
        rows = cursor.fetchall()
        
        preferences = []
        for row in rows:
            preferences.append({
                'id': row[0],
                'preference_type': row[1],
                'context': row[2],
                'preference_data': json.loads(row[3]),
                'confidence_score': row[4],
                'usage_count': row[5],
                'last_updated': row[6]
            })
        
        conn.close()
        return preferences
        
    except Exception as e:
        print(f"Error retrieving user preferences: {e}")
        return [] 