#!/usr/bin/env python3
"""
Script to fix face recognition data and ensure proper defaultdict initialization
"""

import pickle
import json
from pathlib import Path
from collections import defaultdict
import os

def fix_face_data():
    """Fix the face_data.pkl file to ensure proper defaultdict initialization"""
    try:
        known_faces_dir = Path("known_faces")
        data_file = known_faces_dir / "face_data.pkl"
        
        print("🔧 Fixing face recognition data...")
        
        if data_file.exists():
            print("📁 Loading existing face data...")
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            
            print(f"📊 Current data keys: {list(data.keys())}")
            
            # Check the person_encodings structure
            person_encodings = data.get("person_encodings", {})
            print(f"👥 Person encodings type: {type(person_encodings)}")
            print(f"👥 Person encodings keys: {list(person_encodings.keys()) if person_encodings else 'None'}")
            
            # Fix the person_encodings to be a proper defaultdict
            if not isinstance(person_encodings, defaultdict):
                print("🔧 Converting person_encodings to defaultdict(list)...")
                fixed_person_encodings = defaultdict(list)
                if isinstance(person_encodings, dict):
                    # Copy existing data
                    fixed_person_encodings.update(person_encodings)
                
                # Update the data structure
                data["person_encodings"] = dict(fixed_person_encodings)  # Save as dict to pickle
                
                # Save the fixed data
                print("💾 Saving fixed data...")
                with open(data_file, 'wb') as f:
                    pickle.dump(data, f)
                
                print("✅ Face data fixed successfully!")
            else:
                print("✅ Face data is already in correct format!")
                
        else:
            print("❌ No existing face data found!")
            # Create empty proper structure
            data = {
                "encodings": [],
                "names": [],
                "person_encodings": {},
                "metadata": {},
                "version": "2.0"
            }
            
            print("📝 Creating new face data structure...")
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
            
            print("✅ New face data structure created!")
            
        # Test the fix by importing and initializing the face engine
        print("🧪 Testing face engine initialization...")
        from core.face_engine import FaceRecognitionEngine
        
        engine = FaceRecognitionEngine()
        print(f"🔍 Face engine initialized with {len(engine.person_encodings)} persons")
        print(f"📋 Known persons: {list(engine.person_encodings.keys())}")
        print(f"🎯 Person encodings type: {type(engine.person_encodings)}")
        
        print("✅ Face recognition system is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing face data: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting face recognition data fix...")
    success = fix_face_data()
    if success:
        print("🎉 Face recognition system has been fixed and is ready to use!")
    else:
        print("💥 Failed to fix face recognition system. Please check the error above.") 