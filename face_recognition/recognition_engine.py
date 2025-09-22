"""
Face recognition processing engine - Enhanced version
Extracted from face_utils.py recognition functions with better error handling
"""
import numpy as np
import cv2
import logging
from typing import Tuple, Optional, List
from deepface import DeepFace
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings

from config.settings import MODEL_NAME, DETECTOR_BACKEND, EMBEDDING_SIZE, RECOGNITION_THRESHOLD
from face_recognition.image_utils import (
    ensure_rgb, resize_embedding_to_512, validate_image_quality,
    detect_face_in_image, preprocess_image_for_embedding
)

logger = logging.getLogger(__name__)

class FaceRecognitionEngine:
    """Enhanced face recognition processing engine with better error handling"""
    
    def __init__(self):
        self.model_name = MODEL_NAME
        self.detector_backend = DETECTOR_BACKEND
        self.embedding_size = EMBEDDING_SIZE
        self.recognition_threshold = RECOGNITION_THRESHOLD
        
        # Try to initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize DeepFace models"""
        try:
            logger.info("Initializing face recognition models...")
            # Pre-load models by running a test
            test_image = np.ones((224, 224, 3), dtype=np.uint8) * 128
            DeepFace.represent(
                img_path=test_image,
                model_name=self.model_name,
                detector_backend='skip',  # Skip detection for test
                enforce_detection=False
            )
            logger.info("Face recognition models initialized successfully")
        except Exception as e:
            logger.warning(f"Model initialization warning: {e}")
    
    def generate_embedding(self, image, debug_mode: bool = False) -> Optional[np.ndarray]:
        """Generate face embedding from image with enhanced debugging"""
        try:
            if debug_mode:
                logger.info("Starting embedding generation...")
            
            # Input validation
            if image is None:
                logger.error("Input image is None")
                return None
            
            if len(image.shape) != 3:
                logger.error(f"Invalid image shape: {image.shape}")
                return None
            
            # Validate image quality first
            is_valid, message = validate_image_quality(image)
            if not is_valid:
                logger.warning(f"Image quality validation failed: {message}")
                if debug_mode:
                    return None  # Strict mode
                # Continue anyway in non-debug mode
            
            # Try multiple approaches for embedding generation
            embedding = self._try_multiple_detection_approaches(image, debug_mode)
            
            if embedding is not None:
                # Validate and resize embedding
                embedding = resize_embedding_to_512(embedding)
                
                # Normalize embedding
                embedding_norm = np.linalg.norm(embedding)
                if embedding_norm > 0:
                    embedding = embedding / embedding_norm
                
                if debug_mode:
                    logger.info(f"Successfully generated embedding of size {embedding.shape[0]}")
                
                return embedding
            else:
                logger.error("Failed to generate embedding with all approaches")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            if debug_mode:
                import traceback
                logger.error(traceback.format_exc())
            return None
    
    def _try_multiple_detection_approaches(self, image, debug_mode: bool = False) -> Optional[np.ndarray]:
        """Try multiple detection backends and approaches"""
        
        # Approach 1: Original detector backend with face detection
        try:
            if debug_mode:
                logger.info(f"Trying approach 1: {self.detector_backend} with face detection")
            
            rgb_image = ensure_rgb(image)
            
            embedding_result = DeepFace.represent(
                img_path=rgb_image,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=True
            )
            
            return self._extract_embedding_from_result(embedding_result)
            
        except Exception as e:
            if debug_mode:
                logger.warning(f"Approach 1 failed: {e}")
        
        # Approach 2: Skip face detection (use whole image)
        try:
            if debug_mode:
                logger.info("Trying approach 2: Skip detection (whole image)")
            
            rgb_image = ensure_rgb(image)
            
            embedding_result = DeepFace.represent(
                img_path=rgb_image,
                model_name=self.model_name,
                detector_backend='skip',
                enforce_detection=False
            )
            
            return self._extract_embedding_from_result(embedding_result)
            
        except Exception as e:
            if debug_mode:
                logger.warning(f"Approach 2 failed: {e}")
        
        # Approach 3: Try with OpenCV face detection + crop
        try:
            if debug_mode:
                logger.info("Trying approach 3: OpenCV detection + crop")
            
            face_detected, face_message, face_region = detect_face_in_image(image)
            
            if face_detected and face_region is not None:
                rgb_face = ensure_rgb(face_region)
                
                embedding_result = DeepFace.represent(
                    img_path=rgb_face,
                    model_name=self.model_name,
                    detector_backend='skip',
                    enforce_detection=False
                )
                
                return self._extract_embedding_from_result(embedding_result)
            
        except Exception as e:
            if debug_mode:
                logger.warning(f"Approach 3 failed: {e}")
        
        # Approach 4: Different detector backends
        alternative_backends = ['opencv', 'mtcnn', 'ssd', 'dlib']
        
        for backend in alternative_backends:
            if backend == self.detector_backend:
                continue  # Skip already tried
            
            try:
                if debug_mode:
                    logger.info(f"Trying approach 4: {backend} backend")
                
                rgb_image = ensure_rgb(image)
                
                embedding_result = DeepFace.represent(
                    img_path=rgb_image,
                    model_name=self.model_name,
                    detector_backend=backend,
                    enforce_detection=False
                )
                
                return self._extract_embedding_from_result(embedding_result)
                
            except Exception as e:
                if debug_mode:
                    logger.warning(f"Backend {backend} failed: {e}")
                continue
        
        return None
    
    def _extract_embedding_from_result(self, embedding_result) -> Optional[np.ndarray]:
        """Extract embedding array from DeepFace result"""
        try:
            if isinstance(embedding_result, list) and len(embedding_result) > 0:
                embedding = np.array(embedding_result[0]['embedding'], dtype=np.float32)
            elif isinstance(embedding_result, dict) and 'embedding' in embedding_result:
                embedding = np.array(embedding_result['embedding'], dtype=np.float32)
            else:
                logger.error(f"Unexpected embedding result format: {type(embedding_result)}")
                return None
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return None
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            emb1 = np.array(embedding1, dtype=np.float32)
            emb2 = np.array(embedding2, dtype=np.float32)
            
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            similarity = np.clip(similarity, -1.0, 1.0)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def euclidean_distance(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate Euclidean distance between two embeddings"""
        try:
            emb1 = np.array(embedding1, dtype=np.float32)
            emb2 = np.array(embedding2, dtype=np.float32)
            
            distance = np.linalg.norm(emb1 - emb2)
            return float(distance)
            
        except Exception as e:
            logger.error(f"Error calculating Euclidean distance: {e}")
            return float('inf')
    
    def recognize_face(self, input_image, known_embeddings: List[Tuple], debug_mode: bool = False) -> Tuple[bool, Optional[dict], float]:
        """Recognize face in input image against known embeddings"""
        try:
            # Generate embedding for input image
            input_embedding = self.generate_embedding(input_image, debug_mode)
            if input_embedding is None:
                return False, None, 0.0
            
            best_similarity = 0.0
            best_match = None
            
            # Compare with all known embeddings
            for student_id, name, roll_number, known_embedding in known_embeddings:
                try:
                    similarity = self.cosine_similarity(input_embedding, known_embedding)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = {
                            'student_id': student_id,
                            'name': name,
                            'roll_number': roll_number
                        }
                        
                except Exception as e:
                    logger.warning(f"Error comparing with student {name}: {e}")
                    continue
            
            # Check if best match meets threshold
            if best_similarity >= self.recognition_threshold:
                logger.info(f"Face recognized: {best_match['name']} (confidence: {best_similarity:.3f})")
                return True, best_match, best_similarity
            else:
                logger.info(f"No match found. Best similarity: {best_similarity:.3f}")
                return False, None, best_similarity
                
        except Exception as e:
            logger.error(f"Error in face recognition: {e}")
            return False, None, 0.0
    
    def batch_generate_embeddings(self, images: List[np.ndarray], debug_mode: bool = False) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple images with progress tracking"""
        embeddings = []
        successful_count = 0
        
        for i, image in enumerate(images):
            logger.info(f"Processing image {i+1}/{len(images)}")
            embedding = self.generate_embedding(image, debug_mode)
            
            if embedding is not None:
                successful_count += 1
            
            embeddings.append(embedding)
        
        logger.info(f"Successfully generated {successful_count}/{len(images)} embeddings")
        return embeddings
    
    def validate_embedding_quality(self, embedding: np.ndarray) -> Tuple[bool, str]:
        """Validate the quality of generated embedding"""
        try:
            if embedding is None:
                return False, "Embedding is None"
            
            if not isinstance(embedding, np.ndarray):
                return False, "Embedding is not a numpy array"
            
            if embedding.shape[0] != self.embedding_size:
                return False, f"Embedding size {embedding.shape[0]} != expected {self.embedding_size}"
            
            # Check for NaN or infinite values
            if np.isnan(embedding).any():
                return False, "Embedding contains NaN values"
            
            if np.isinf(embedding).any():
                return False, "Embedding contains infinite values"
            
            # Check if embedding is all zeros (invalid)
            if np.allclose(embedding, 0):
                return False, "Embedding is all zeros"
            
            # Check embedding norm
            norm = np.linalg.norm(embedding)
            if norm < 0.1:
                return False, f"Embedding norm too small: {norm}"
            
            return True, "Embedding is valid"
            
        except Exception as e:
            logger.error(f"Error validating embedding: {e}")
            return False, f"Validation error: {str(e)}"

    def debug_image_processing(self, image) -> dict:
        """Debug information about image processing"""
        debug_info = {
            'image_shape': None,
            'image_dtype': None,
            'image_range': None,
            'quality_check': None,
            'face_detection': None,
            'embedding_generation': None
        }
        
        try:
            # Basic image info
            debug_info['image_shape'] = image.shape if image is not None else None
            debug_info['image_dtype'] = str(image.dtype) if image is not None else None
            debug_info['image_range'] = f"[{image.min()}, {image.max()}]" if image is not None else None
            
            # Quality check
            is_valid, message = validate_image_quality(image)
            debug_info['quality_check'] = {'valid': is_valid, 'message': message}
            
            # Face detection
            face_detected, face_message, face_region = detect_face_in_image(image)
            debug_info['face_detection'] = {
                'detected': face_detected,
                'message': face_message,
                'has_region': face_region is not None
            }
            
            # Try embedding generation
            embedding = self.generate_embedding(image, debug_mode=True)
            debug_info['embedding_generation'] = {
                'success': embedding is not None,
                'embedding_shape': embedding.shape if embedding is not None else None
            }
            
        except Exception as e:
            debug_info['error'] = str(e)
        
        return debug_info
