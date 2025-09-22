"""
Student management business logic - Enhanced with debugging
"""
import streamlit as st
import logging
import uuid
from typing import List, Dict, Tuple, Optional
from database.student_repository import StudentRepository
from face_recognition.recognition_engine import FaceRecognitionEngine

logger = logging.getLogger(__name__)

class StudentService:
    """Enhanced student management with debugging capabilities"""
    
    def __init__(self):
        self.student_repo = StudentRepository()
        self.face_engine = FaceRecognitionEngine()
    
    def add_student_with_photos(self, name: str, roll_number: str, email: str, 
                              phone: str, course: str, images: List, 
                              debug_mode: bool = False) -> Tuple[bool, str]:
        """Add student with face embeddings from multiple photos"""
        try:
            # Validate inputs
            if not all([name.strip(), roll_number.strip(), email.strip()]):
                return False, "Name, roll number, and email are required"
            
            if len(images) < 2:
                return False, "At least 2 photos are required for registration"
            
            if len(images) > 5:
                return False, "Maximum 5 photos allowed for registration"
            
            # Show debug information if enabled
            if debug_mode:
                self._show_debug_info(images)
            
            # Generate embeddings for all images
            embeddings_data = []
            successful_embeddings = 0
            processing_results = []
            
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, image in enumerate(images):
                status_text.text(f"Processing image {i+1}/{len(images)}...")
                progress_bar.progress((i + 1) / len(images))
                
                # Generate unique photo ID
                photo_id = f"{roll_number}_{uuid.uuid4().hex[:8]}"
                
                # Debug image processing if needed
                if debug_mode:
                    debug_info = self.face_engine.debug_image_processing(image)
                    processing_results.append({
                        'image_index': i + 1,
                        'debug_info': debug_info
                    })
                    self._display_debug_results(i + 1, debug_info)
                
                # Generate embedding
                embedding = self.face_engine.generate_embedding(image, debug_mode=debug_mode)
                
                if embedding is not None:
                    # Validate embedding quality
                    is_valid, validation_message = self.face_engine.validate_embedding_quality(embedding)
                    if is_valid:
                        embeddings_data.append((photo_id, embedding))
                        successful_embeddings += 1
                        logger.info(f"Generated valid embedding for photo {i+1}")
                        
                        if debug_mode:
                            st.success(f"✅ Photo {i+1}: Embedding generated successfully")
                    else:
                        logger.warning(f"Invalid embedding for photo {i+1}: {validation_message}")
                        if debug_mode:
                            st.warning(f"⚠️ Photo {i+1}: Invalid embedding - {validation_message}")
                else:
                    logger.warning(f"Failed to generate embedding for photo {i+1}")
                    if debug_mode:
                        st.error(f"❌ Photo {i+1}: Failed to generate embedding")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Show final debug summary
            if debug_mode:
                self._show_final_debug_summary(successful_embeddings, len(images), processing_results)
            
            # Check if we have enough valid embeddings
            if successful_embeddings < 2:
                error_msg = f"Only {successful_embeddings} valid embeddings generated. Minimum 2 required."
                
                if debug_mode:
                    st.error("🚨 **Embedding Generation Failed**")
                    st.error(error_msg)
                    
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        **Common issues and solutions:**
                        
                        1. **Poor Image Quality**:
                           - Use well-lit photos
                           - Ensure faces are clearly visible
                           - Avoid blurry or low-resolution images
                        
                        2. **Face Detection Issues**:
                           - Make sure faces are facing the camera
                           - Remove sunglasses, hats, or masks
                           - Use photos with single person only
                        
                        3. **Image Format Issues**:
                           - Use PNG, JPG, or JPEG formats
                           - Ensure images are not corrupted
                           - Try smaller file sizes (< 10MB)
                        
                        4. **Model Loading Issues**:
                           - Restart the application
                           - Check internet connection (for model download)
                           - Ensure sufficient memory available
                        """)
                
                return False, error_msg
            
            # Add student to database
            success, message = self.student_repo.add_student_with_photos(
                name, roll_number, email, phone, course, embeddings_data
            )
            
            if success:
                logger.info(f"Student {name} added with {successful_embeddings} face embeddings")
                return True, f"Student {name} added successfully with {successful_embeddings} face photos"
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error adding student: {e}")
            return False, f"Error adding student: {str(e)}"
    
    def _show_debug_info(self, images):
        """Show debug information about uploaded images"""
        st.markdown("### 🔍 Debug Information")
        
        with st.expander("📊 Image Analysis", expanded=True):
            for i, image in enumerate(images):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(image, caption=f"Photo {i+1}", width=150)
                
                with col2:
                    st.write(f"**Photo {i+1} Details:**")
                    st.write(f"- Shape: {image.shape}")
                    st.write(f"- Data type: {image.dtype}")
                    st.write(f"- Value range: [{image.min()}, {image.max()}]")
                    
                st.divider()
    
    def _display_debug_results(self, image_index: int, debug_info: dict):
        """Display debug results for a single image"""
        with st.expander(f"🔍 Photo {image_index} Debug Results"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Image Properties:**")
                st.json({
                    'shape': debug_info.get('image_shape'),
                    'dtype': debug_info.get('image_dtype'),
                    'range': debug_info.get('image_range')
                })
            
            with col2:
                st.write("**Quality & Detection:**")
                
                quality_check = debug_info.get('quality_check', {})
                if quality_check.get('valid'):
                    st.success(f"✅ Quality: {quality_check.get('message')}")
                else:
                    st.error(f"❌ Quality: {quality_check.get('message')}")
                
                face_detection = debug_info.get('face_detection', {})
                if face_detection.get('detected'):
                    st.success(f"✅ Face: {face_detection.get('message')}")
                else:
                    st.error(f"❌ Face: {face_detection.get('message')}")
                
                embedding_gen = debug_info.get('embedding_generation', {})
                if embedding_gen.get('success'):
                    st.success(f"✅ Embedding: Generated {embedding_gen.get('embedding_shape')}")
                else:
                    st.error("❌ Embedding: Generation failed")
    
    def _show_final_debug_summary(self, successful_embeddings: int, total_images: int, processing_results: list):
        """Show final debug summary"""
        st.markdown("### 📋 Processing Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Images", total_images)
        
        with col2:
            st.metric("Successful Embeddings", successful_embeddings)
        
        with col3:
            success_rate = (successful_embeddings / total_images) * 100 if total_images > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Show detailed results
        if processing_results:
            st.markdown("### 🔬 Detailed Results")
            
            for result in processing_results:
                image_idx = result['image_index']
                debug_info = result['debug_info']
                
                embedding_success = debug_info.get('embedding_generation', {}).get('success', False)
                
                if embedding_success:
                    st.success(f"✅ Photo {image_idx}: Successfully processed")
                else:
                    st.error(f"❌ Photo {image_idx}: Processing failed")
                    
                    # Show specific failure reasons
                    quality_issue = not debug_info.get('quality_check', {}).get('valid', True)
                    face_issue = not debug_info.get('face_detection', {}).get('detected', False)
                    
                    if quality_issue:
                        st.warning(f"   - Quality issue: {debug_info.get('quality_check', {}).get('message')}")
                    
                    if face_issue:
                        st.warning(f"   - Face detection: {debug_info.get('face_detection', {}).get('message')}")

    # Add debug mode to existing methods
    def get_all_students(self) -> List[Dict]:
        """Get all active students"""
        return self.student_repo.get_all_students()
    
    # ... rest of your existing methods remain the same

    
    def get_all_students(self) -> List[Dict]:
        """Get all active students"""
        return self.student_repo.get_all_students()
    
    def delete_student(self, student_id: int) -> Tuple[bool, str]:
        """Delete student"""
        return self.student_repo.delete_student(student_id)
    
    def recognize_student(self, image) -> Tuple[bool, Optional[Dict], float]:
        """Recognize student from image"""
        try:
            # Get all student embeddings
            student_embeddings = self.student_repo.get_student_embeddings()
            
            if not student_embeddings:
                return False, None, 0.0
            
            # Use face recognition engine to identify student
            is_recognized, student_info, confidence = self.face_engine.recognize_face(
                image, student_embeddings
            )
            
            if is_recognized:
                logger.info(f"Student recognized: {student_info['name']} with confidence {confidence:.3f}")
            else:
                logger.info(f"Student not recognized. Best confidence: {confidence:.3f}")
            
            return is_recognized, student_info, confidence
            
        except Exception as e:
            logger.error(f"Error recognizing student: {e}")
            return False, None, 0.0
    
    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student details by ID"""
        try:
            students = self.student_repo.get_all_students()
            for student in students:
                if student['id'] == student_id:
                    return student
            return None
        except Exception as e:
            logger.error(f"Error getting student by ID: {e}")
            return None
    
    def search_students(self, search_term: str) -> List[Dict]:
        """Search students by name, roll number, or email"""
        try:
            all_students = self.student_repo.get_all_students()
            search_term = search_term.lower().strip()
            
            if not search_term:
                return all_students
            
            filtered_students = []
            for student in all_students:
                if (search_term in student['name'].lower() or 
                    search_term in student['roll_number'].lower() or 
                    (student['email'] and search_term in student['email'].lower())):
                    filtered_students.append(student)
            
            return filtered_students
            
        except Exception as e:
            logger.error(f"Error searching students: {e}")
            return []
    
    def get_students_by_course(self, course: str) -> List[Dict]:
        """Get students filtered by course"""
        try:
            all_students = self.student_repo.get_all_students()
            return [s for s in all_students if s.get('course', '').lower() == course.lower()]
        except Exception as e:
            logger.error(f"Error getting students by course: {e}")
            return []
    
    def update_student_info(self, student_id: int, updates: Dict) -> Tuple[bool, str]:
        """Update student information"""
        try:
            # This would require adding an update method to the repository
            # For now, return not implemented
            return False, "Student update functionality not implemented yet"
        except Exception as e:
            logger.error(f"Error updating student: {e}")
            return False, f"Error updating student: {str(e)}"
    
    def delete_all_students(self) -> Tuple[bool, str]:
        """Delete all students and their data"""
        return self.student_repo.delete_all_students()
    
    def get_student_statistics(self) -> Dict:
        """Get student statistics"""
        try:
            students = self.student_repo.get_all_students()
            
            if not students:
                return {
                    'total_students': 0,
                    'by_course': {},
                    'with_photos': 0,
                    'without_photos': 0
                }
            
            # Calculate statistics
            by_course = {}
            with_photos = 0
            without_photos = 0
            
            for student in students:
                # Course statistics
                course = student.get('course', 'Unknown')
                by_course[course] = by_course.get(course, 0) + 1
                
                # Photo statistics
                if student.get('photo_count', 0) > 0:
                    with_photos += 1
                else:
                    without_photos += 1
            
            return {
                'total_students': len(students),
                'by_course': by_course,
                'with_photos': with_photos,
                'without_photos': without_photos
            }
            
        except Exception as e:
            logger.error(f"Error getting student statistics: {e}")
            return {
                'total_students': 0,
                'by_course': {},
                'with_photos': 0,
                'without_photos': 0
            }
