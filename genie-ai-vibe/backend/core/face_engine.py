import cv2
import face_recognition
import numpy as np
from typing import List, Dict, Optional
import json
from PIL import Image
import io
from pathlib import Path
import logging
import hashlib
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)

class FaceRecognitionEngine:
    def __init__(self, known_faces_dir: str = "known_faces", confidence_threshold: float = 0.55):
        self.known_faces_dir = Path(known_faces_dir)
        self.confidence_threshold = confidence_threshold
        
        # Use multiple encodings per person for better accuracy
        self.known_face_encodings = []  # List of all encodings
        self.known_face_names = []      # Corresponding names for each encoding
        self.person_encodings = defaultdict(list)  # Dict: name -> list of encodings
        self.known_faces_metadata = {}
        
        # Recognition settings - optimized for speed and accuracy
        self.face_detection_model = "hog"  # "hog" for speed, switch to "cnn" if accuracy is more important
        self.num_jitters = 3  # Further optimized for speed while maintaining accuracy
        self.face_locations_model = "hog"
        
        # Quality thresholds
        self.min_face_size = 50  # Increased for better quality
        self.max_faces_per_person = 4  # Optimal for ensemble accuracy
        
        # Performance optimizations
        self.face_detection_scale = 0.6  # Better balance of speed vs accuracy
        self.max_image_size = 1000  # Allow slightly larger images for better quality
        
        # Advanced ensemble settings for better accuracy
        self.use_ensemble_method = True
        self.ensemble_weights = [0.4, 0.3, 0.2, 0.1]  # Weight newer encodings more
        self.dynamic_threshold = True  # Adjust threshold based on image quality
        self.min_threshold = 0.45  # Minimum threshold for good quality images
        self.max_threshold = 0.75  # Maximum threshold for poor quality images
        
        # Temporal consistency tracking for better accuracy
        self.recognition_history = []  # Store recent recognition results
        self.history_window = 10  # Number of recent recognitions to track
        self.temporal_bonus = 0.05  # Bonus for consistent recognition
        
        # Create directories
        self.known_faces_dir.mkdir(exist_ok=True)
        (self.known_faces_dir / "metadata").mkdir(exist_ok=True)
        (self.known_faces_dir / "photos").mkdir(exist_ok=True)
        
        self.load_known_faces()
        logger.info(f"Face Recognition Engine initialized with {len(set(self.known_face_names))} known persons, {len(self.known_face_encodings)} total encodings")
    
    def _extract_face_encoding(self, image_array: np.ndarray, face_location: tuple = None) -> Optional[np.ndarray]:
        """Extract face encoding from image using face_recognition library"""
        try:
            # If no face location provided, detect faces first
            if face_location is None:
                face_locations = face_recognition.face_locations(
                    image_array, 
                    model=self.face_detection_model
                )
                if not face_locations:
                    return None
                face_location = face_locations[0]  # Use the first face found
            
            # Check face size
            top, right, bottom, left = face_location
            face_width = right - left
            face_height = bottom - top
            
            if face_width < self.min_face_size or face_height < self.min_face_size:
                logger.warning(f"Face too small: {face_width}x{face_height}")
                return None
            
            # Extract face encoding
            encodings = face_recognition.face_encodings(
                image_array, 
                [face_location], 
                num_jitters=self.num_jitters
            )
            
            if encodings:
                return encodings[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting face encoding: {str(e)}")
            return None
    
    def _calculate_similarity_score(self, face_encoding: np.ndarray, person_name: str) -> float:
        """Calculate similarity score using ensemble method with weighted voting"""
        if person_name not in self.person_encodings:
            return 0.0
        
        person_encodings = self.person_encodings[person_name]
        if len(person_encodings) == 0:
            return 0.0
            
        # Calculate distances to all encodings for this person
        distances = face_recognition.face_distance(person_encodings, face_encoding)
        
        if not self.use_ensemble_method or len(person_encodings) == 1:
            # Simple method for single encoding
            min_distance = np.min(distances)
            return self._distance_to_similarity(min_distance)
        
        # Advanced ensemble method with weighted voting
        similarities = []
        for i, distance in enumerate(distances):
            similarity = self._distance_to_similarity(distance)
            
            # Apply ensemble weight (newer encodings get higher weight)
            weight_idx = min(i, len(self.ensemble_weights) - 1)
            weight = self.ensemble_weights[weight_idx]
            weighted_similarity = similarity * weight
            similarities.append(weighted_similarity)
        
        # Ensemble aggregation strategies
        weighted_average = np.sum(similarities)
        best_match = np.max([self._distance_to_similarity(d) for d in distances])
        min_distance = np.min(distances)
        
        # Statistical validation
        std_dev = np.std(distances)
        consistency_bonus = 1.0
        
        # Penalize if encodings are too inconsistent
        if std_dev > 0.15:
            consistency_bonus = 0.8
        elif std_dev < 0.05:
            consistency_bonus = 1.1  # Bonus for very consistent encodings
        
        # Combine different scoring methods
        final_score = (
            weighted_average * 0.5 +           # Weighted ensemble vote
            best_match * 0.3 +                 # Best single match
            (1.0 - min_distance) * 0.2         # Distance-based score
        ) * consistency_bonus
        
        # Apply stricter thresholds for ensemble validation
        if len(person_encodings) >= 3:
            # For well-established persons, require more consensus
            matches_above_threshold = sum(1 for d in distances if d <= 0.5)
            consensus_ratio = matches_above_threshold / len(distances)
            
            if consensus_ratio < 0.6:  # Less than 60% consensus
                final_score *= 0.7  # Significant penalty
        
        return min(1.0, final_score)
    
    def _distance_to_similarity(self, distance: float) -> float:
        """Convert face distance to similarity score with improved mapping"""
        # More aggressive thresholds based on research
        if distance <= 0.25:  # Excellent match
            return 1.0 - (distance / 0.25) * 0.1  # Scale to 0.9-1.0
        elif distance <= 0.35:  # Very good match  
            return 0.9 - ((distance - 0.25) / 0.1) * 0.15  # Scale to 0.75-0.9
        elif distance <= 0.45:  # Good match
            return 0.75 - ((distance - 0.35) / 0.1) * 0.25  # Scale to 0.5-0.75
        elif distance <= 0.6:   # Acceptable match
            return 0.5 - ((distance - 0.45) / 0.15) * 0.3   # Scale to 0.2-0.5
        else:  # Poor match
            return max(0.0, 0.2 - ((distance - 0.6) / 0.4) * 0.2)  # Scale to 0-0.2
    
    def _validate_face_quality(self, image_array: np.ndarray, face_location: tuple) -> Dict:
        """Validate face quality for recognition"""
        top, right, bottom, left = face_location
        face_width = right - left
        face_height = bottom - top
        
        # Extract face region with some padding
        padding = 10
        face_top = max(0, top - padding)
        face_bottom = min(image_array.shape[0], bottom + padding)
        face_left = max(0, left - padding)
        face_right = min(image_array.shape[1], right + padding)
        
        face_region = image_array[face_top:face_bottom, face_left:face_right]
        
        quality_score = 1.0
        issues = []
        
        # Check size - faces should be reasonably large
        if face_width < 60 or face_height < 60:
            quality_score *= 0.5
            issues.append("small_face")
        elif face_width < 100 or face_height < 100:
            quality_score *= 0.8
            issues.append("medium_face")
        
        # Check aspect ratio - faces should be roughly proportioned
        aspect_ratio = face_width / face_height
        if aspect_ratio < 0.6 or aspect_ratio > 1.6:
            quality_score *= 0.6
            issues.append("unusual_aspect_ratio")
        
        # Check brightness and contrast
        if len(face_region.shape) == 3:
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)
        else:
            gray_face = face_region
        
        brightness = np.mean(gray_face)
        if brightness < 40:
            quality_score *= 0.5
            issues.append("too_dark")
        elif brightness > 220:
            quality_score *= 0.7
            issues.append("too_bright")
        elif brightness < 80 or brightness > 180:
            quality_score *= 0.9
            issues.append("suboptimal_lighting")
        
        # Check contrast - good faces have varied pixel values
        contrast = np.std(gray_face)
        if contrast < 25:
            quality_score *= 0.6
            issues.append("low_contrast")
        elif contrast < 40:
            quality_score *= 0.8
            issues.append("medium_contrast")
        
        # Check for blur using Laplacian variance
        laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        if laplacian_var < 50:
            quality_score *= 0.4
            issues.append("blurry")
        elif laplacian_var < 100:
            quality_score *= 0.7
            issues.append("slight_blur")
        
        # Check if face is at edge of image (might be cut off)
        img_height, img_width = image_array.shape[:2]
        edge_threshold = 20
        if (left < edge_threshold or top < edge_threshold or 
            right > img_width - edge_threshold or bottom > img_height - edge_threshold):
            quality_score *= 0.8
            issues.append("edge_face")
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "is_good_quality": quality_score > 0.7 and len(issues) <= 2,
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": laplacian_var
        }
    
    def add_known_person(self, name: str, photo_data: bytes, metadata: Dict = None) -> Dict:
        try:
            image = Image.open(io.BytesIO(photo_data))
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image_array = np.array(image)
            
            # Detect faces
            face_locations = face_recognition.face_locations(
                image_array, 
                model=self.face_detection_model
            )
            
            if not face_locations:
                return {"success": False, "error": "No face detected", "face_count": 0}
            
            if len(face_locations) > 1:
                logger.warning(f"Multiple faces detected for {name}, using the largest one")
                # Select the largest face
                face_sizes = [(right-left)*(bottom-top) for top, right, bottom, left in face_locations]
                largest_face_idx = np.argmax(face_sizes)
                face_location = face_locations[largest_face_idx]
            else:
                face_location = face_locations[0]
            
            # Validate face quality
            quality_check = self._validate_face_quality(image_array, face_location)
            
            # Require higher quality for training data to prevent misidentification
            if quality_check["quality_score"] < 0.6:
                return {
                    "success": False, 
                    "error": f"Face quality too low for training: {quality_check['issues']}. Please use a clearer photo with good lighting.",
                    "quality_score": quality_check["quality_score"],
                    "issues": quality_check["issues"]
                }
            
            if not quality_check["is_good_quality"]:
                logger.warning(f"Suboptimal face quality for {name}: {quality_check['issues']}")
            
            # Extract face encoding
            face_encoding = self._extract_face_encoding(image_array, face_location)
            
            if face_encoding is None:
                return {"success": False, "error": "Could not extract face features", "face_count": len(face_locations)}
            
            # Additional validation: if this person already exists, check consistency with existing encodings
            if name in self.person_encodings:
                existing_encodings = self.person_encodings[name]
                distances = face_recognition.face_distance(existing_encodings, face_encoding)
                avg_distance = np.mean(distances)
                
                # If the new encoding is very different from existing ones, it might be a different person
                if avg_distance > 0.7:
                    return {
                        "success": False,
                        "error": f"New photo looks very different from existing photos of {name}. Please verify this is the same person.",
                        "distance_to_existing": float(avg_distance)
                    }
                
                # Add to existing person's encodings (max limit)
                if len(self.person_encodings[name]) >= self.max_faces_per_person:
                    # Replace the oldest encoding
                    old_encoding_idx = self.known_face_names.index(name)
                    self.known_face_encodings[old_encoding_idx] = face_encoding
                    self.person_encodings[name][0] = face_encoding
                else:
                    # Add new encoding
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_names.append(name)
                    # Ensure the person_encodings entry is a list
                    if not isinstance(self.person_encodings[name], list):
                        self.person_encodings[name] = []
                    self.person_encodings[name].append(face_encoding)
            else:
                # New person
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                # Ensure the person_encodings entry is a list
                if name not in self.person_encodings:
                    self.person_encodings[name] = []
                self.person_encodings[name].append(face_encoding)
            
            # Save the photo with timestamp
            photo_filename = f"{name}_{len(self.person_encodings[name])}.jpg"
            photo_path = self.known_faces_dir / "photos" / photo_filename
            image.save(photo_path, "JPEG", quality=95)
            
            # Save metadata
            person_metadata = {
                "name": name,
                "added_date": str(np.datetime64('now')),
                "photo_paths": [str(photo_path)],
                "access_level": metadata.get("access_level", "standard") if metadata else "standard",
                "notes": metadata.get("notes", "") if metadata else "",
                "encoding_count": len(self.person_encodings[name]),
                "quality_score": quality_check["quality_score"],
                "quality_issues": quality_check["issues"]
            }
            
            # Update existing metadata or create new
            if name in self.known_faces_metadata:
                existing_metadata = self.known_faces_metadata[name]
                existing_metadata["photo_paths"].append(str(photo_path))
                existing_metadata["encoding_count"] = len(self.person_encodings[name])
                existing_metadata["last_updated"] = str(np.datetime64('now'))
            else:
                self.known_faces_metadata[name] = person_metadata
            
            self._save_face_data()
            
            return {
                "success": True,
                "message": f"Successfully added/updated {name}",
                "person_count": len(self.person_encodings),
                "encoding_count": len(self.person_encodings[name]),
                "face_locations": len(face_locations),
                "quality_score": quality_check["quality_score"],
                "quality_issues": quality_check["issues"]
            }
            
        except Exception as e:
            logger.error(f"Error adding person {name}: {str(e)}")
            return {"success": False, "error": f"Failed to process image: {str(e)}"}
    
    def recognize_face(self, image_data: bytes) -> Dict:
        try:
            # Load and preprocess image
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image_array = np.array(image)
            
            # Preprocess image for better recognition
            image_array = self._preprocess_image(image_array)
            
            # Create smaller version for face detection (speed optimization)
            height, width = image_array.shape[:2]
            small_height = int(height * self.face_detection_scale)
            small_width = int(width * self.face_detection_scale)
            small_image = cv2.resize(image_array, (small_width, small_height))
            
            # Detect faces on smaller image
            small_face_locations = face_recognition.face_locations(
                small_image, 
                model=self.face_detection_model,
                number_of_times_to_upsample=0
            )
            
            if not small_face_locations:
                return {
                    "success": True,
                    "faces_detected": 0,
                    "recognized_persons": [],
                    "message": "No faces detected"
                }
            
            # Scale face locations back to original size
            scale_factor = 1.0 / self.face_detection_scale
            face_locations = []
            for top, right, bottom, left in small_face_locations:
                face_locations.append((
                    int(top * scale_factor),
                    int(right * scale_factor), 
                    int(bottom * scale_factor),
                    int(left * scale_factor)
                ))
            
            # Get face encodings from original size image
            face_encodings = face_recognition.face_encodings(
                image_array, 
                face_locations, 
                num_jitters=self.num_jitters
            )
            
            recognized_persons = []
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Validate face quality
                quality_check = self._validate_face_quality(image_array, face_location)
                
                # Skip very poor quality faces
                if quality_check["quality_score"] < 0.3:
                    logger.warning(f"Skipping poor quality face: {quality_check['issues']}")
                    continue
                
                # Get dynamic threshold based on image quality
                dynamic_threshold = self._get_dynamic_threshold(quality_check)
                
                # Find best match among all known persons
                best_match_name = "Unknown"
                best_similarity = 0.0
                best_metadata = {}
                
                if self.person_encodings:
                    best_scores = []  # Track all similarity scores for additional validation
                    
                    for person_name in self.person_encodings.keys():
                        similarity = self._calculate_similarity_score(face_encoding, person_name)
                        best_scores.append((similarity, person_name))
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            if similarity >= dynamic_threshold:
                                best_match_name = person_name
                                best_metadata = self.known_faces_metadata.get(person_name, {})
                    
                    # Multi-layer validation system
                    validation_passed = True
                    rejection_reason = None
                    
                    # Layer 1: Confidence threshold validation
                    if best_similarity < dynamic_threshold:
                        validation_passed = False
                        rejection_reason = f"Below confidence threshold: {best_similarity:.3f} < {dynamic_threshold:.3f}"
                    
                    # Layer 2: Ambiguity detection (competitive scoring)
                    elif len(best_scores) >= 2:
                        best_scores.sort(reverse=True)
                        first_score = best_scores[0][0]
                        second_score = best_scores[1][0]
                        
                        # Calculate margin between best and second-best
                        margin = first_score - second_score
                        required_margin = 0.12 if quality_check["quality_score"] > 0.7 else 0.18
                        
                        if margin < required_margin and first_score < 0.85:
                            validation_passed = False
                            rejection_reason = f"Ambiguous match: margin {margin:.3f} < {required_margin:.3f}"
                            best_match_name = "Unknown"
                            best_similarity = 0.0
                            best_metadata = {}
                    
                    # Layer 3: Quality-based confidence adjustment
                    if validation_passed and best_match_name != "Unknown":
                        # Apply final quality adjustments
                        if quality_check["quality_score"] > 0.8:
                            best_similarity = min(1.0, best_similarity * 1.02)  # Small bonus for excellent quality
                        elif quality_check["quality_score"] < 0.5:
                            best_similarity *= 0.9  # Penalty for poor quality
                        
                        # Final validation check
                        if best_similarity < dynamic_threshold:
                            validation_passed = False
                            rejection_reason = f"Failed final validation: {best_similarity:.3f} < {dynamic_threshold:.3f}"
                            best_match_name = "Unknown"
                            best_similarity = 0.0
                            best_metadata = {}
                    
                    # Log detailed validation results
                    if best_match_name != "Unknown":
                        logger.info(f"✅ Validated match: {best_match_name} - Score: {best_similarity:.3f} - Threshold: {dynamic_threshold:.3f} - Quality: {quality_check['quality_score']:.3f}")
                    else:
                        logger.info(f"❌ Rejected: {rejection_reason if rejection_reason else 'Unknown reason'}")
                
                # Apply temporal consistency bonus
                if best_match_name != "Unknown":
                    best_similarity = self._apply_temporal_consistency(best_match_name, best_similarity)
                
                top, right, bottom, left = face_location
                
                recognized_persons.append({
                    "name": best_match_name,
                    "confidence": float(best_similarity),
                    "face_location": {"top": top, "right": right, "bottom": bottom, "left": left},
                    "access_level": best_metadata.get("access_level", "none" if best_match_name == "Unknown" else "standard"),
                    "metadata": best_metadata,
                    "face_quality": quality_check["quality_score"],
                    "quality_issues": quality_check["issues"],
                    "dynamic_threshold": dynamic_threshold,
                    "validation_details": {
                        "brightness": quality_check.get("brightness", 0),
                        "contrast": quality_check.get("contrast", 0),
                        "sharpness": quality_check.get("sharpness", 0)
                    }
                })
                
                # Update recognition history
                self._update_recognition_history(best_match_name)
            
            # Log recognition results for debugging
            if recognized_persons:
                for person in recognized_persons:
                    logger.info(f"Recognition: {person['name']} - Confidence: {person['confidence']:.3f} - Quality: {person['face_quality']:.3f}")
            
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
    
    def list_known_persons(self) -> Dict:
        try:
            persons_list = []
            for person_name in self.person_encodings.keys():
                metadata = self.known_faces_metadata.get(person_name, {})
                photo_paths = metadata.get("photo_paths", [])
                
                persons_list.append({
                    "name": person_name,
                    "access_level": metadata.get("access_level", "standard"),
                    "added_date": metadata.get("added_date", "Unknown"),
                    "notes": metadata.get("notes", ""),
                    "encoding_count": len(self.person_encodings[person_name]),
                    "photo_count": len(photo_paths),
                    "quality_score": metadata.get("quality_score", 0.0),
                    "has_photos": len(photo_paths) > 0
                })
            
            return {
                "success": True,
                "total_persons": len(persons_list),
                "total_encodings": len(self.known_face_encodings),
                "persons": persons_list
            }
            
        except Exception as e:
            logger.error(f"Error listing persons: {str(e)}")
            return {"success": False, "error": f"Failed to list persons: {str(e)}", "persons": []}
    
    def remove_known_person(self, name: str) -> Dict:
        try:
            if name not in self.person_encodings:
                return {"success": False, "error": f"Person '{name}' not found"}
            
            # Remove all encodings for this person
            person_encodings_to_remove = self.person_encodings[name]
            
            # Remove from main lists (in reverse order to maintain indices)
            indices_to_remove = []
            for i, known_name in enumerate(self.known_face_names):
                if known_name == name:
                    indices_to_remove.append(i)
            
            for idx in reversed(indices_to_remove):
                del self.known_face_encodings[idx]
                del self.known_face_names[idx]
            
            # Remove from person_encodings dict
            del self.person_encodings[name]
            
            # Remove photos
            if name in self.known_faces_metadata:
                photo_paths = self.known_faces_metadata[name].get("photo_paths", [])
                for photo_path in photo_paths:
                    try:
                        Path(photo_path).unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Could not remove photo {photo_path}: {e}")
                
                # Remove metadata
                del self.known_faces_metadata[name]
            
            self._save_face_data()
            
            return {
                "success": True,
                "message": f"Successfully removed {name}",
                "remaining_persons": len(self.person_encodings)
            }
            
        except Exception as e:
            logger.error(f"Error removing person {name}: {str(e)}")
            return {"success": False, "error": f"Failed to remove person: {str(e)}"}
    
    def get_person_photo(self, name: str) -> Optional[bytes]:
        try:
            if name not in self.known_faces_metadata:
                return None
            
            photo_paths = self.known_faces_metadata[name].get("photo_paths", [])
            if not photo_paths:
                return None
            
            # Return the most recent photo
            photo_path = Path(photo_paths[-1])
            if photo_path.exists():
                return photo_path.read_bytes()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting photo for {name}: {str(e)}")
            return None
    
    def update_confidence_threshold(self, threshold: float) -> Dict:
        try:
            if not 0.1 <= threshold <= 1.0:
                return {"success": False, "error": "Threshold must be between 0.1 and 1.0"}
            
            old_threshold = self.confidence_threshold
            self.confidence_threshold = threshold
            
            return {
                "success": True,
                "message": f"Confidence threshold updated from {old_threshold} to {threshold}",
                "old_threshold": old_threshold,
                "new_threshold": threshold
            }
            
        except Exception as e:
            logger.error(f"Error updating confidence threshold: {str(e)}")
            return {"success": False, "error": f"Failed to update threshold: {str(e)}"}
    
    def load_known_faces(self):
        try:
            # Load from pickle file for better performance
            data_file = self.known_faces_dir / "face_data.pkl"
            
            if data_file.exists():
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                
                self.known_face_encodings = data.get("encodings", [])
                self.known_face_names = data.get("names", [])
                # Ensure person_encodings is always a defaultdict(list)
                person_encodings_data = data.get("person_encodings", {})
                self.person_encodings = defaultdict(list)
                self.person_encodings.update(person_encodings_data)
                self.known_faces_metadata = data.get("metadata", {})
                
                logger.info(f"Loaded {len(self.person_encodings)} known persons from pickle storage")
                logger.info(f"Known persons: {list(self.person_encodings.keys())}")
            else:
                logger.info("No pickle file found, trying to load from legacy format")
                # Try to load from old format
                self._load_legacy_format()
                
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")
            self.known_face_encodings = []
            self.known_face_names = []
            self.person_encodings = defaultdict(list)
            self.known_faces_metadata = {}
    
    def _load_legacy_format(self):
        """Load from the old numpy/json format"""
        try:
            encodings_file = self.known_faces_dir / "face_encodings.npy"
            names_file = self.known_faces_dir / "face_names.json"
            metadata_file = self.known_faces_dir / "metadata" / "face_metadata.json"
            
            if encodings_file.exists() and names_file.exists():
                logger.info(f"Loading legacy encodings from {encodings_file}")
                encodings = np.load(encodings_file, allow_pickle=True)
                with open(names_file, 'r') as f:
                    names = json.load(f)
                
                logger.info(f"Legacy format found: {len(encodings)} encodings, {len(names)} names")
                logger.info(f"Names: {names}")
                
                # Convert to new format
                self.known_face_encodings = encodings.tolist()
                self.known_face_names = names
                
                # Group by person
                for encoding, name in zip(self.known_face_encodings, self.known_face_names):
                    self.person_encodings[name].append(encoding)
                
                if metadata_file.exists():
                    logger.info(f"Loading metadata from {metadata_file}")
                    with open(metadata_file, 'r') as f:
                        self.known_faces_metadata = json.load(f)
                
                # Save in new format
                self._save_face_data()
                logger.info(f"Converted legacy format: {len(self.person_encodings)} persons")
                logger.info(f"Person encodings keys: {list(self.person_encodings.keys())}")
            else:
                logger.warning(f"Legacy files not found: encodings={encodings_file.exists()}, names={names_file.exists()}")
                
        except Exception as e:
            logger.error(f"Error loading legacy format: {str(e)}")
    
    def _save_face_data(self):
        try:
            # Save in pickle format for better performance
            data_file = self.known_faces_dir / "face_data.pkl"
            
            data = {
                "encodings": self.known_face_encodings,
                "names": self.known_face_names,
                "person_encodings": dict(self.person_encodings),
                "metadata": self.known_faces_metadata,
                "version": "2.0"
            }
            
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Also save in JSON format for backup
            backup_file = self.known_faces_dir / "metadata" / "face_metadata.json"
            with open(backup_file, 'w') as f:
                json.dump(self.known_faces_metadata, f, indent=2)
                
            logger.info("Face data saved to persistent storage")
            
        except Exception as e:
            logger.error(f"Error saving face data: {str(e)}")
    
    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
        """Preprocess image for optimal face recognition"""
        # Get original dimensions
        height, width = image_array.shape[:2]
        
        # Resize if image is too large (for speed)
        if width > self.max_image_size or height > self.max_image_size:
            scale = self.max_image_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image_array = cv2.resize(image_array, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Enhance image quality for better face detection
        # Normalize brightness and contrast
        if len(image_array.shape) == 3:
            # Convert to LAB color space for better lighting adjustment
            lab = cv2.cvtColor(image_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge back
            enhanced = cv2.merge([l, a, b])
            image_array = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        # Slight sharpening for better edge detection
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        image_array = cv2.filter2D(image_array, -1, kernel)
        
        # Ensure values are in valid range
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)
        
        return image_array

    def _get_dynamic_threshold(self, face_quality: Dict, image_context: Dict = None) -> float:
        """Calculate dynamic threshold based on image quality and context"""
        if not self.dynamic_threshold:
            return self.confidence_threshold
        
        base_threshold = self.confidence_threshold
        quality_score = face_quality.get("quality_score", 0.5)
        brightness = face_quality.get("brightness", 128)
        contrast = face_quality.get("contrast", 50)
        sharpness = face_quality.get("sharpness", 100)
        
        # Adjust threshold based on image quality factors
        threshold_adjustment = 0.0
        
        # Quality score adjustment
        if quality_score > 0.8:
            threshold_adjustment -= 0.05  # Lower threshold for high quality
        elif quality_score < 0.5:
            threshold_adjustment += 0.1   # Higher threshold for poor quality
        
        # Brightness adjustment
        if brightness < 60 or brightness > 200:
            threshold_adjustment += 0.05  # Poor lighting
        
        # Contrast adjustment  
        if contrast < 30:
            threshold_adjustment += 0.05  # Low contrast
        
        # Sharpness adjustment
        if sharpness < 80:
            threshold_adjustment += 0.08  # Blurry image
        elif sharpness > 200:
            threshold_adjustment -= 0.03  # Very sharp image
        
        # Apply adjustments within bounds
        dynamic_threshold = base_threshold + threshold_adjustment
        dynamic_threshold = max(self.min_threshold, min(self.max_threshold, dynamic_threshold))
        
        return dynamic_threshold

    def _apply_temporal_consistency(self, person_name: str, confidence: float) -> float:
        """Apply temporal consistency bonus based on recent recognition history"""
        if not self.recognition_history or person_name == "Unknown":
            return confidence
        
        # Count recent recognitions of this person
        recent_count = sum(1 for entry in self.recognition_history[-5:] if entry == person_name)
        
        # Apply temporal bonus for consistent recognition
        if recent_count >= 2:
            temporal_bonus = min(self.temporal_bonus * recent_count, 0.15)
            logger.debug(f"Temporal bonus for {person_name}: +{temporal_bonus:.3f} (recent: {recent_count})")
            return min(1.0, confidence + temporal_bonus)
        
        return confidence
    
    def _update_recognition_history(self, person_name: str):
        """Update the recognition history with the latest result"""
        self.recognition_history.append(person_name)
        
        # Keep only recent history
        if len(self.recognition_history) > self.history_window:
            self.recognition_history = self.recognition_history[-self.history_window:] 