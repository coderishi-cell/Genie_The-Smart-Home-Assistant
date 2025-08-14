import cv2
import face_recognition
import numpy as np
from typing import List, Dict, Optional, Tuple
import os
import json
import base64
from PIL import Image
import io
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FaceRecognitionEngine:
    """
    Advanced Face Recognition Engine for Smart Home Security
    
    Features:
    - Face encoding and recognition using state-of-the-art algorithms
    - Known persons database management
    - Real-time face detection and recognition
    - Confidence scoring and threshold management
    - Photo management for known persons
    """
    
    def __init__(self, known_faces_dir: str = "known_faces", confidence_threshold: float = 0.4):
        self.known_faces_dir = Path(known_faces_dir)
        self.confidence_threshold = confidence_threshold
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_faces_metadata = {}
        
        # Create directories if they don't exist
        self.known_faces_dir.mkdir(exist_ok=True)
        (self.known_faces_dir / "metadata").mkdir(exist_ok=True)
        
        # Load existing known faces
        self.load_known_faces()
        
        logger.info(f"Face Recognition Engine initialized with {len(self.known_face_names)} known persons")
    
    def add_known_person(self, name: str, photo_data: bytes, metadata: Dict = None) -> Dict:
        """
        Add a new known person to the database
        
        Args:
            name: Person's name/identifier
            photo_data: Image data as bytes
            metadata: Additional information about the person
            
        Returns:
            Dict with success status and details
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(photo_data))
            image_array = np.array(image)
            
            # Convert RGB to BGR if needed (OpenCV uses BGR)
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Detect faces in the image
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                return {
                    "success": False,
                    "error": "No face detected in the provided image",
                    "face_count": 0
                }
            
            if len(face_locations) > 1:
                logger.warning(f"Multiple faces detected for {name}, using the first one")
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            if not face_encodings:
                return {
                    "success": False,
                    "error": "Could not encode the detected face",
                    "face_count": len(face_locations)
                }
            
            # Use the first face encoding
            face_encoding = face_encodings[0]
            
            # Check if person already exists
            if name in self.known_face_names:
                # Update existing person
                existing_index = self.known_face_names.index(name)
                self.known_face_encodings[existing_index] = face_encoding
                logger.info(f"Updated face encoding for existing person: {name}")
            else:
                # Add new person
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                logger.info(f"Added new person: {name}")
            
            # Save the photo
            photo_path = self.known_faces_dir / f"{name}.jpg"
            image.save(photo_path, "JPEG")
            
            # Save metadata
            person_metadata = {
                "name": name,
                "added_date": str(np.datetime64('now')),
                "photo_path": str(photo_path),
                "face_encoding_shape": face_encoding.shape,
                "access_level": metadata.get("access_level", "standard") if metadata else "standard",
                "notes": metadata.get("notes", "") if metadata else ""
            }
            
            self.known_faces_metadata[name] = person_metadata
            
            # Save to persistent storage
            self._save_face_data()
            
            return {
                "success": True,
                "message": f"Successfully added/updated {name}",
                "person_count": len(self.known_face_names),
                "face_locations": len(face_locations)
            }
            
        except Exception as e:
            logger.error(f"Error adding known person {name}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to process image: {str(e)}"
            }
    
    def recognize_face(self, image_data: bytes) -> Dict:
        """
        Recognize faces in the provided image
        
        Args:
            image_data: Image data as bytes
            
        Returns:
            Dict with recognition results
        """
        try:
            # Convert bytes to image array
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Convert RGB to BGR if needed
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image_array)
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            if not face_locations:
                return {
                    "success": True,
                    "faces_detected": 0,
                    "recognized_persons": [],
                    "message": "No faces detected in the image"
                }
            
            recognized_persons = []
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Compare with known faces
                if self.known_face_encodings:
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    confidence = 1 - face_distances[best_match_index]
                    
                    # Debug logging for confidence scores
                    best_match_name = self.known_face_names[best_match_index]
                    logger.info(f"Face recognition: Best match '{best_match_name}' with confidence {confidence:.3f} (threshold: {self.confidence_threshold})")
                    
                    if confidence >= self.confidence_threshold:
                        person_name = self.known_face_names[best_match_index]
                        person_metadata = self.known_faces_metadata.get(person_name, {})
                        
                        logger.info(f"Face recognized: {person_name} (confidence: {confidence:.3f})")
                        
                        recognized_persons.append({
                            "name": person_name,
                            "confidence": float(confidence),
                            "face_location": {
                                "top": face_location[0],
                                "right": face_location[1],
                                "bottom": face_location[2],
                                "left": face_location[3]
                            },
                            "access_level": person_metadata.get("access_level", "standard"),
                            "metadata": person_metadata
                        })
                    else:
                        logger.info(f"Face detected but confidence {confidence:.3f} below threshold {self.confidence_threshold}")
                        recognized_persons.append({
                            "name": "Unknown",
                            "confidence": float(confidence),
                            "face_location": {
                                "top": face_location[0],
                                "right": face_location[1],
                                "bottom": face_location[2],
                                "left": face_location[3]
                            },
                            "access_level": "none",
                            "metadata": {}
                        })
                else:
                    recognized_persons.append({
                        "name": "Unknown",
                        "confidence": 0.0,
                        "face_location": {
                            "top": face_location[0],
                            "right": face_location[1],
                            "bottom": face_location[2],
                            "left": face_location[3]
                        },
                        "access_level": "none",
                        "metadata": {}
                    })
            
            return {
                "success": True,
                "faces_detected": len(face_locations),
                "recognized_persons": recognized_persons,
                "timestamp": str(np.datetime64('now'))
            }
            
        except Exception as e:
            logger.error(f"Error in face recognition: {str(e)}")
            return {
                "success": False,
                "error": f"Recognition failed: {str(e)}",
                "faces_detected": 0,
                "recognized_persons": []
            }
    
    def remove_known_person(self, name: str) -> Dict:
        """
        Remove a person from the known faces database
        
        Args:
            name: Person's name to remove
            
        Returns:
            Dict with operation status
        """
        try:
            if name not in self.known_face_names:
                return {
                    "success": False,
                    "error": f"Person '{name}' not found in database"
                }
            
            # Remove from lists
            index = self.known_face_names.index(name)
            self.known_face_names.pop(index)
            self.known_face_encodings.pop(index)
            
            # Remove metadata
            if name in self.known_faces_metadata:
                del self.known_faces_metadata[name]
            
            # Remove photo file
            photo_path = self.known_faces_dir / f"{name}.jpg"
            if photo_path.exists():
                photo_path.unlink()
            
            # Save updated data
            self._save_face_data()
            
            logger.info(f"Removed person: {name}")
            return {
                "success": True,
                "message": f"Successfully removed {name}",
                "remaining_persons": len(self.known_face_names)
            }
            
        except Exception as e:
            logger.error(f"Error removing person {name}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to remove person: {str(e)}"
            }
    
    def list_known_persons(self) -> Dict:
        """
        List all known persons in the database
        
        Returns:
            Dict with list of known persons and their metadata
        """
        try:
            persons_list = []
            for name in self.known_face_names:
                metadata = self.known_faces_metadata.get(name, {})
                persons_list.append({
                    "name": name,
                    "access_level": metadata.get("access_level", "standard"),
                    "added_date": metadata.get("added_date", "Unknown"),
                    "notes": metadata.get("notes", ""),
                    "has_photo": (self.known_faces_dir / f"{name}.jpg").exists()
                })
            
            return {
                "success": True,
                "total_persons": len(persons_list),
                "persons": persons_list
            }
            
        except Exception as e:
            logger.error(f"Error listing known persons: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to list persons: {str(e)}",
                "persons": []
            }
    
    def get_person_photo(self, name: str) -> Optional[bytes]:
        """
        Get the photo data for a known person
        
        Args:
            name: Person's name
            
        Returns:
            Photo data as bytes or None if not found
        """
        try:
            photo_path = self.known_faces_dir / f"{name}.jpg"
            if photo_path.exists():
                with open(photo_path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error getting photo for {name}: {str(e)}")
            return None
    
    def load_known_faces(self):
        """Load known faces from persistent storage"""
        try:
            # Load face encodings
            encodings_file = self.known_faces_dir / "face_encodings.npy"
            names_file = self.known_faces_dir / "face_names.json"
            metadata_file = self.known_faces_dir / "metadata" / "face_metadata.json"
            
            if encodings_file.exists() and names_file.exists():
                self.known_face_encodings = np.load(encodings_file).tolist()
                
                with open(names_file, 'r') as f:
                    self.known_face_names = json.load(f)
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        self.known_faces_metadata = json.load(f)
                
                logger.info(f"Loaded {len(self.known_face_names)} known persons from storage")
            else:
                logger.info("No existing face database found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_faces_metadata = {}
    
    def _save_face_data(self):
        """Save face data to persistent storage"""
        try:
            # Save face encodings
            encodings_file = self.known_faces_dir / "face_encodings.npy"
            names_file = self.known_faces_dir / "face_names.json"
            metadata_file = self.known_faces_dir / "metadata" / "face_metadata.json"
            
            if self.known_face_encodings:
                np.save(encodings_file, np.array(self.known_face_encodings))
            
            with open(names_file, 'w') as f:
                json.dump(self.known_face_names, f)
            
            with open(metadata_file, 'w') as f:
                json.dump(self.known_faces_metadata, f, indent=2)
                
            logger.info("Face data saved to persistent storage")
            
        except Exception as e:
            logger.error(f"Error saving face data: {str(e)}")
    
    def update_confidence_threshold(self, new_threshold: float) -> Dict:
        """
        Update the confidence threshold for face recognition
        
        Args:
            new_threshold: New threshold value (0.0 to 1.0)
            
        Returns:
            Dict with operation status
        """
        try:
            if not 0.0 <= new_threshold <= 1.0:
                return {
                    "success": False,
                    "error": "Threshold must be between 0.0 and 1.0"
                }
            
            old_threshold = self.confidence_threshold
            self.confidence_threshold = new_threshold
            
            logger.info(f"Updated confidence threshold from {old_threshold} to {new_threshold}")
            
            return {
                "success": True,
                "message": f"Confidence threshold updated to {new_threshold}",
                "old_threshold": old_threshold,
                "new_threshold": new_threshold
            }
            
        except Exception as e:
            logger.error(f"Error updating confidence threshold: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update threshold: {str(e)}"
            } 