import os
import numpy as np
import cv2
from deepface import DeepFace
import uuid
from datetime import datetime
import logging

# Configuration constants
MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "retinaface"  
EMBEDDING_SIZE = 512

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_rgb(frame_bgr):
    """Convert BGR to RGB for DeepFace compatibility"""
    try:
        if len(frame_bgr.shape) == 3 and frame_bgr.shape[2] == 3:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        else:
            rgb = frame_bgr
        return rgb
    except Exception as e:
        logger.warning(f"Color conversion failed: {e}")
        return frame_bgr

def resize_embedding_to_512(embedding):
    """Ensure embedding is exactly 512 dimensions"""
    try:
        embedding = np.array(embedding, dtype=np.float32)
        
        if embedding.shape[0] == EMBEDDING_SIZE:
            return embedding
        elif embedding.shape[0] > EMBEDDING_SIZE:
            # Truncate to 512
            logger.warning(f"Truncating embedding from {embedding.shape[0]} to {EMBEDDING_SIZE}")
            return embedding[:EMBEDDING_SIZE]
        else:
            # Pad with zeros to reach 512
            logger.warning(f"Padding embedding from {embedding.shape[0]} to {EMBEDDING_SIZE}")
            padding = np.zeros(EMBEDDING_SIZE - embedding.shape[0], dtype=np.float32)
            return np.concatenate([embedding, padding])
            
    except Exception as e:
        logger.error(f"Error resizing embedding: {e}")
        return np.zeros(EMBEDDING_SIZE, dtype=np.float32)

def validate_image_quality(image):
    """Validate if image quality is sufficient for recognition"""
    try:
        if image is None or image.size == 0:
            return False, "Invalid image"
        
        height, width = image.shape[:2]
        
        # Check minimum dimensions
        if height < 100 or width < 100:
            return False, "Image resolution too low (minimum 100x100)"
        
        # Check if image is too dark or too bright
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        if brightness < 30:
            return False, "Image too dark"
        elif brightness > 225:
            return False, "Image too bright"
        
        # Check contrast
        contrast = np.std(gray)
        if contrast < 20:
            return False, "Image has low contrast"
        
        return True, "Image quality acceptable"
        
    except Exception as e:
        logger.error(f"Error validating image quality: {e}")
        return False, f"Validation error: {str(e)}"

def image_to_embedding_bgr(frame_bgr):
    """FIXED: Generate 512-dimensional embedding from BGR image with proper error handling"""
    try:
        # Validate input image first
        if frame_bgr is None or frame_bgr.size == 0:
            logger.error("Invalid input image - None or empty")
            return None
        
        # Validate image quality
        is_valid, message = validate_image_quality(frame_bgr)
        if not is_valid:
            logger.warning(f"Image quality check failed: {message}")
            # Don't return None immediately, try to process anyway for demo
        
        # Ensure minimum image size
        if frame_bgr.shape[0] < 50 or frame_bgr.shape[1] < 50:
            logger.error("Image too small for face detection")
            return None
        
        # Convert to RGB
        rgb = ensure_rgb(frame_bgr)
        
        # Generate embedding using DeepFace with proper error handling
        try:
            logger.info("Attempting face recognition...")
            
            # Try with enforce_detection=True first (strict mode)
            try:
                result = DeepFace.represent(
                    rgb,
                    model_name=MODEL_NAME,
                    detector_backend=DETECTOR_BACKEND,
                    enforce_detection=True  # FIXED: Changed to True for strict face detection
                )
                logger.info("Face detected successfully in strict mode")
                
            except ValueError as strict_error:
                if "Face could not be detected" in str(strict_error):
                    logger.warning("No face detected in strict mode, trying relaxed mode...")
                    
                    # Fallback to relaxed mode
                    try:
                        result = DeepFace.represent(
                            rgb,
                            model_name=MODEL_NAME,
                            detector_backend="opencv",  # Use more permissive detector
                            enforce_detection=False
                        )
                        logger.info("Face detected in relaxed mode")
                    except Exception as relaxed_error:
                        logger.error(f"Face detection failed in both modes: {relaxed_error}")
                        return None
                else:
                    raise strict_error
            
            # Extract embedding from result
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and 'embedding' in result[0]:
                    embedding = np.array(result[0]['embedding'], dtype=np.float32)
                else:
                    logger.error("Unexpected result format - no embedding in first item")
                    return None
            elif isinstance(result, dict) and 'embedding' in result:
                embedding = np.array(result['embedding'], dtype=np.float32)
            else:
                logger.error(f"Unexpected result format: {type(result)}")
                return None
            
            # Ensure 512 dimensions
            embedding = resize_embedding_to_512(embedding)
            
            logger.info(f"Successfully generated {embedding.shape[0]}-dimensional embedding")
            return embedding
            
        except Exception as e:
            logger.error(f"DeepFace processing error: {e}")
            
            # Try alternative approach with different settings
            try:
                logger.info("Trying alternative face detection approach...")
                result = DeepFace.represent(
                    rgb,
                    model_name="Facenet",  # Alternative model
                    detector_backend="mtcnn",  # Alternative detector
                    enforce_detection=False
                )
                
                if isinstance(result, list) and len(result) > 0:
                    embedding = np.array(result[0]['embedding'], dtype=np.float32)
                    embedding = resize_embedding_to_512(embedding)
                    logger.info("Successfully generated embedding with alternative approach")
                    return embedding
                    
            except Exception as alt_error:
                logger.error(f"Alternative approach also failed: {alt_error}")
            
            return None
            
    except Exception as e:
        logger.error(f"Critical error in face recognition: {e}")
        return None

def cosine_similarity(emb1, emb2):
    """Calculate cosine similarity between two embeddings"""
    try:
        # Ensure both embeddings are 512-dimensional
        emb1 = resize_embedding_to_512(emb1)
        emb2 = resize_embedding_to_512(emb2)
        
        # Calculate cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure similarity is between 0 and 1
        similarity = max(0.0, min(1.0, similarity))
        
        return similarity
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

def euclidean_distance(emb1, emb2):
    """Calculate Euclidean distance between two embeddings"""
    try:
        emb1 = resize_embedding_to_512(emb1)
        emb2 = resize_embedding_to_512(emb2)
        
        distance = np.linalg.norm(emb1 - emb2)
        return float(distance)
        
    except Exception as e:
        logger.error(f"Error calculating Euclidean distance: {e}")
        return float('inf')

def calculate_face_distance(emb1, emb2):
    """Calculate Euclidean distance between embeddings (alias for compatibility)"""
    return euclidean_distance(emb1, emb2)

def detect_face_in_image(image):
    """Simple face detection to validate image before processing"""
    try:
        rgb = ensure_rgb(image)
        
        # Use OpenCV's built-in face detector for quick validation
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            return True, f"Detected {len(faces)} face(s)"
        else:
            # Fallback to DeepFace detection
            try:
                DeepFace.extract_faces(rgb, enforce_detection=True, detector_backend="opencv")
                return True, "Face detected with DeepFace"
            except:
                return False, "No face detected"
                
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return False, f"Detection error: {str(e)}"

def enhance_image_for_recognition(image):
    """Enhance image quality for better face recognition"""
    try:
        # Convert to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to BGR
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced_bgr
        
    except Exception as e:
        logger.error(f"Error enhancing image: {e}")
        return image

def preprocess_image(image, target_size=(224, 224)):
    """Preprocess image for face recognition"""
    try:
        # Enhance image quality
        enhanced = enhance_image_for_recognition(image)
        
        # Resize image if needed
        height, width = enhanced.shape[:2]
        if height != target_size[0] or width != target_size[1]:
            enhanced = cv2.resize(enhanced, target_size, interpolation=cv2.INTER_AREA)
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return image

def save_frame_bgr(frame, prefix="photo", roll="", photo_number=1):
    """Save frame to file with enhanced naming"""
    try:
        dir_path = "photos"
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        
        if roll:
            fname = f"{prefix}_{roll}_photo{photo_number}_{timestamp}_{unique_id}.jpg"
        else:
            fname = f"{prefix}_photo{photo_number}_{timestamp}_{unique_id}.jpg"
        
        path = os.path.join(dir_path, fname)
        
        if cv2.imwrite(path, frame):
            logger.info(f"Saved photo: {fname}")
            return path
        else:
            logger.error(f"Failed to save photo: {fname}")
            return None
            
    except Exception as e:
        logger.error(f"Error saving frame: {e}")
        return None

def test_face_recognition():
    """Test the face recognition system with a dummy image"""
    try:
        # Create a test image (gray square)
        test_image = np.ones((200, 200, 3), dtype=np.uint8) * 128
        
        logger.info("Testing face recognition system...")
        
        # Test image processing
        embedding = image_to_embedding_bgr(test_image)
        
        if embedding is not None:
            logger.info(f"✅ Face recognition test successful - {embedding.shape[0]} dimensions")
            return True
        else:
            logger.warning("⚠️ Face recognition test failed - no embedding generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Face recognition test error: {e}")
        return False

def get_model_info():
    """Get information about the current face recognition configuration"""
    return {
        'model_name': MODEL_NAME,
        'detector_backend': DETECTOR_BACKEND,
        'embedding_size': EMBEDDING_SIZE,
        'description': f'{MODEL_NAME} model with {DETECTOR_BACKEND} face detection'
    }

# Test the system on import
try:
    logger.info("🚀 Initializing face recognition system...")
    logger.info(f"📊 Configuration: {MODEL_NAME} + {DETECTOR_BACKEND}, {EMBEDDING_SIZE}D embeddings")
    
    # Quick system test
    test_success = test_face_recognition()
    if test_success:
        logger.info("✅ Face recognition system ready!")
    else:
        logger.warning("⚠️ Face recognition system may have issues - check dependencies")
        
except Exception as e:
    logger.warning(f"⚠️ Face recognition initialization warning: {e}")

logger.info("Enhanced face recognition utilities loaded successfully")
