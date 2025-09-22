"""
Student management page component - Complete fixed version with proper form clearing
Extracted from app.py student management functionality
"""
import streamlit as st
import pandas as pd
import numpy as np
import cv2
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StudentManagementPage:
    """Student management page component - complete working version"""
    
    def __init__(self):
        try:
            from services.student_service import StudentService
            self.student_service = StudentService()
        except ImportError:
            self.student_service = None
    
    def render(self):
        """Render student management page"""
        st.markdown("## 👥 Student Management")
        
        tab1, tab2 = st.tabs(["➕ Add Student", "📋 Manage Students"])
        
        with tab1:
            self._render_add_student_tab()
        
        with tab2:
            self._render_manage_students_tab()
    
    def _render_add_student_tab(self):
        """Render add student tab with proper form clearing"""
        st.markdown("### 📸 Register New Student")
        
        # Debug mode toggle
        debug_mode = st.checkbox("🔍 Enable Debug Mode", 
                               help="Show detailed processing information and troubleshooting")
        
        if debug_mode:
            st.info("🐛 Debug mode enabled - You'll see detailed processing information")
        
        # Check if form should be cleared
        if st.session_state.get('clear_student_form', False):
            self._clear_all_form_fields()
            st.session_state.clear_student_form = False
            st.success("🔄 Form cleared! You can now register another student.")
            time.sleep(1)
            st.rerun()
        
        st.markdown("#### 📝 Student Information")
        
        # Student details - simple inputs with proper keys
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "👤 Full Name *", 
                placeholder="Enter student's full name",
                key="student_name",
                help="Enter the full name of the student"
            )
            email = st.text_input(
                "📧 Email Address *", 
                placeholder="student@example.com",
                key="student_email",
                help="Enter unique email address"
            )
            course = st.selectbox(
                "📚 Course *", 
                options=["", "Computer Science", "Civil Engineering", 
                        "Electrical Engineering", "Mechanical Engineering", 
                        "Biomedical Engineering"],
                key="student_course",
                help="Select the student's course/department"
            )
        
        with col2:
            roll_number = st.text_input(
                "🎫 Roll Number *", 
                placeholder="Enter unique roll number",
                key="student_roll",
                help="Enter unique roll number (e.g., CS2024001)"
            )
            phone = st.text_input(
                "📱 Phone Number", 
                placeholder="Enter phone number (optional)",
                key="student_phone",
                help="Optional: Student's contact number"
            )
        
        st.markdown("#### 📸 Face Photos")
        st.info("📌 Upload 2-5 clear photos of the student for better recognition accuracy")
        
        uploaded_files = st.file_uploader(
            "Choose student photos",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload 2-5 clear photos of the student's face for training the recognition model",
            key="student_photos"
        )
        
        # Real-time validation feedback
        self._show_form_validation_feedback(name, roll_number, email, course, uploaded_files)
        
        # Photo preview
        if uploaded_files and len(uploaded_files) <= 5:
            with st.expander("📸 Photo Preview", expanded=True):
                cols = st.columns(min(len(uploaded_files), 5))
                for i, file in enumerate(uploaded_files[:5]):
                    with cols[i]:
                        st.image(file, caption=f"Photo {i+1}", width=100)
        
        st.markdown("---")
        
        # Submit button - always clickable
        if st.button("🎓 Register Student", use_container_width=True, type="primary", key="register_btn"):
            self._handle_form_submission(name, roll_number, email, course, phone, uploaded_files, debug_mode)
    
    def _show_form_validation_feedback(self, name: str, roll_number: str, email: str, course: str, uploaded_files):
        """Show real-time validation feedback"""
        # Required field validation
        missing_fields = []
        if not name:
            missing_fields.append("Full Name")
        if not roll_number:
            missing_fields.append("Roll Number")
        if not email:
            missing_fields.append("Email Address")
        if not course:
            missing_fields.append("Course")
        
        if missing_fields:
            st.warning(f"⚠️ **Required fields:** {', '.join(missing_fields)}")
        
        # Photo validation
        if not uploaded_files:
            st.warning("⚠️ **Photos required:** Upload at least 2 photos")
        elif len(uploaded_files) < 2:
            st.warning("⚠️ **More photos needed:** Upload at least 2 photos for better accuracy")
        elif len(uploaded_files) > 5:
            st.error("❌ **Too many photos:** Maximum 5 photos allowed")
        else:
            st.success(f"✅ **{len(uploaded_files)} photos ready** - Good to register!")
        
        # Email format validation
        if email and '@' not in email:
            st.warning("⚠️ **Email format:** Please enter a valid email address")
        
        # Show completion status
        total_required = 4  # name, roll, email, course
        completed_required = sum([bool(name), bool(roll_number), bool(email), bool(course)])
        photos_ok = uploaded_files and 2 <= len(uploaded_files) <= 5
        
        progress = (completed_required / total_required) * 0.8 + (0.2 if photos_ok else 0)
        
        if progress < 1.0:
            st.progress(progress)
            st.caption(f"Form completion: {progress*100:.0f}%")
    
    def _handle_form_submission(self, name: str, roll_number: str, email: str, course: str, 
                               phone: str, uploaded_files, debug_mode: bool):
        """Handle form submission with validation"""
        # Validation
        if not name:
            st.error("❌ Please enter student's full name")
            return
        elif not roll_number:
            st.error("❌ Please enter roll number")
            return
        elif not email:
            st.error("❌ Please enter email address")
            return
        elif '@' not in email:
            st.error("❌ Please enter a valid email address")
            return
        elif not course:
            st.error("❌ Please select a course")
            return
        elif not uploaded_files:
            st.error("❌ Please upload at least 2 photos")
            return
        elif len(uploaded_files) < 2:
            st.error("❌ Please upload at least 2 photos for better accuracy")
            return
        elif len(uploaded_files) > 5:
            st.error("❌ Maximum 5 photos allowed")
            return
        
        # All validation passed - process registration
        student_data = {
            'name': name.strip(),
            'roll_number': roll_number.strip(),
            'email': email.strip().lower(),
            'phone': phone.strip() if phone else '',
            'course': course
        }
        
        self._handle_student_registration(student_data, uploaded_files, debug_mode)
    
    def _handle_student_registration(self, student_data: Dict, uploaded_files: List, debug_mode: bool = False):
        """Handle student registration process"""
        with st.spinner("🔄 Processing photos and creating student profile..."):
            try:
                # Convert uploaded files to images
                image_data = self._process_uploaded_images(uploaded_files, debug_mode)
                
                if not image_data:
                    st.error("❌ No valid images could be processed")
                    return
                
                # Register student
                success, message = self._add_student_to_database(student_data, image_data)
                
                if success:
                    self._show_registration_success(student_data, len(image_data))
                else:
                    self._show_registration_error(message, debug_mode)
                    
            except Exception as e:
                logger.error(f"Student registration error: {e}")
                st.error(f"❌ Unexpected error during registration: {str(e)}")
                
                if debug_mode:
                    with st.expander("🔧 Debug Information", expanded=True):
                        st.code(f"Error details: {str(e)}")
                        st.exception(e)
    
    def _add_student_to_database(self, student_data: Dict, image_data: List) -> tuple:
        """Add student to database with multiple fallback methods"""
        try:
            # Try service first if available
            if self.student_service:
                try:
                    success, message = self.student_service.add_student_with_photos(
                        name=student_data['name'],
                        roll_number=student_data['roll_number'],
                        email=student_data['email'],
                        phone=student_data['phone'],
                        course=student_data['course'],
                        images=image_data
                    )
                    return success, message
                except Exception as e:
                    logger.warning(f"Service failed, trying direct database: {e}")
            
            # Fallback to direct database function
            from db import add_student_with_photos
            
            success = add_student_with_photos(
                name=student_data['name'],
                roll_number=student_data['roll_number'],
                email=student_data['email'],
                phone=student_data['phone'],
                course=student_data['course'],
                images=image_data
            )
            
            if success:
                return True, "Student registered successfully"
            else:
                return False, "Failed to register student - check for duplicate roll number or email"
                
        except Exception as e:
            logger.error(f"Database registration error: {e}")
            return False, f"Database error: {str(e)}"
    
    def _process_uploaded_images(self, uploaded_files: List, debug_mode: bool = False) -> List[np.ndarray]:
        """Process uploaded image files with detailed feedback"""
        image_data = []
        processed_count = 0
        
        if debug_mode:
            st.markdown("### 📊 Image Processing Details")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing image {i+1}/{len(uploaded_files)}...")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            try:
                # Process each image
                processed_image = self._convert_uploaded_file(uploaded_file, debug_mode, i+1)
                
                if processed_image is not None:
                    image_data.append(processed_image)
                    processed_count += 1
                    
                    if debug_mode:
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            # Display processed image
                            display_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
                            st.image(display_image, caption=f"Processed {i+1}", width=150)
                        
                        with col2:
                            st.success(f"✅ Image {i+1}: Successfully processed")
                            st.write(f"**File:** {uploaded_file.name}")
                            st.write(f"**Size:** {uploaded_file.size} bytes")
                            st.write(f"**Shape:** {processed_image.shape}")
                            st.write(f"**Type:** {processed_image.dtype}")
                else:
                    if debug_mode:
                        st.error(f"❌ Image {i+1}: Processing failed")
                        st.write(f"**File:** {uploaded_file.name}")
                        st.write(f"**Size:** {uploaded_file.size} bytes")
                    else:
                        st.warning(f"⚠️ Could not process image {i+1}: {uploaded_file.name}")
                        
            except Exception as e:
                logger.warning(f"Error processing image {i+1}: {e}")
                if debug_mode:
                    st.error(f"❌ Image {i+1}: Exception occurred")
                    st.code(f"Error: {str(e)}")
                else:
                    st.warning(f"⚠️ Error processing image {i+1}")
        
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Show processing summary
        success_rate = (processed_count / len(uploaded_files)) * 100 if uploaded_files else 0
        
        if debug_mode:
            st.info(f"📊 **Processing Summary:** {processed_count}/{len(uploaded_files)} images processed ({success_rate:.1f}% success rate)")
        
        if success_rate < 100:
            st.warning(f"⚠️ Only {processed_count} out of {len(uploaded_files)} images could be processed successfully")
        
        return image_data
    
    def _convert_uploaded_file(self, uploaded_file, debug_mode: bool = False, image_num: int = 0) -> Optional[np.ndarray]:
        """Convert uploaded file to OpenCV format with comprehensive error handling"""
        try:
            # Read file bytes
            file_bytes = uploaded_file.read()
            
            if len(file_bytes) == 0:
                if debug_mode:
                    st.error(f"❌ Image {image_num}: Empty file")
                return None
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(file_bytes, np.uint8)
            
            # Decode image using OpenCV
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                if debug_mode:
                    st.error(f"❌ Image {image_num}: Could not decode image")
                    st.write("💡 **Tip:** Try converting the image to JPG format")
                return None
            
            # Validate image dimensions
            if image.shape[0] < 50 or image.shape[1] < 50:
                if debug_mode:
                    st.error(f"❌ Image {image_num}: Image too small ({image.shape[1]}x{image.shape[0]})")
                    st.write("💡 **Tip:** Use images at least 50x50 pixels")
                return None
            
            # Ensure proper format (3 channels, BGR)
            if len(image.shape) == 2:
                # Grayscale to BGR
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                if debug_mode:
                    st.info(f"🔄 Image {image_num}: Converted grayscale to BGR")
            elif len(image.shape) == 3:
                if image.shape[2] == 4:
                    # RGBA to BGR
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
                    if debug_mode:
                        st.info(f"🔄 Image {image_num}: Converted RGBA to BGR")
                elif image.shape[2] != 3:
                    if debug_mode:
                        st.error(f"❌ Image {image_num}: Unsupported channel count: {image.shape[2]}")
                    return None
            
            # Resize if too large (for performance)
            max_dimension = 1024
            height, width = image.shape[:2]
            
            if height > max_dimension or width > max_dimension:
                if height > width:
                    new_height = max_dimension
                    new_width = int((width * max_dimension) / height)
                else:
                    new_width = max_dimension
                    new_height = int((height * max_dimension) / width)
                
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
                if debug_mode:
                    st.info(f"🔄 Image {image_num}: Resized from {width}x{height} to {new_width}x{new_height}")
            
            return image
            
        except Exception as e:
            logger.error(f"Error converting image {image_num}: {e}")
            if debug_mode:
                st.error(f"❌ Image {image_num}: Conversion error")
                st.code(f"Error: {str(e)}")
            return None
    
    def _show_registration_success(self, student_data: Dict, photo_count: int):
        """Show successful registration message with reliable form clearing"""
        st.success("🎉 Student registered successfully!")
        st.balloons()
        
        # Registration summary
        st.markdown("#### 📊 Registration Summary")
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            st.info(f"**👤 Name:** {student_data['name']}")
            st.info(f"**🎫 Roll Number:** {student_data['roll_number']}")
            st.info(f"**📧 Email:** {student_data['email']}")
        
        with summary_col2:
            st.info(f"**📚 Course:** {student_data['course']}")
            st.info(f"**📞 Phone:** {student_data['phone'] if student_data['phone'] else 'Not provided'}")
            st.info(f"**📸 Photos Processed:** {photo_count}")
        
        st.success(f"✨ **{student_data['name']}** has been successfully registered!")
        
        # Auto-clear form with countdown
        st.markdown("---")
        st.info("🔄 **Form will be cleared automatically in 3 seconds...**")
        
        # Show countdown
        countdown_placeholder = st.empty()
        for i in range(3, 0, -1):
            countdown_placeholder.info(f"🔄 Clearing form in {i} seconds... (Refresh page to cancel)")
            time.sleep(1)
        
        countdown_placeholder.empty()
        
        # Clear form and rerun
        st.session_state.clear_student_form = True
        st.rerun()
    
    def _clear_all_form_fields(self):
        """Clear all form fields from session state"""
        # List of all form field keys
        form_keys_to_clear = [
            'student_name',
            'student_email', 
            'student_course',
            'student_roll',
            'student_phone',
            'student_photos'
        ]
        
        # Clear specific form fields
        for key in form_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear all keys that start with 'student_'
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('student_')]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear file uploader cache (important for file uploads)
        if 'FormSubmitter:student_form-Submit' in st.session_state:
            del st.session_state['FormSubmitter:student_form-Submit']
        
        logger.info("All student form fields cleared")
    
    def _show_registration_error(self, message: str, debug_mode: bool = False):
        """Show registration error message with troubleshooting help"""
        st.error(f"❌ Registration failed: {message}")
        st.warning("📝 **Form data preserved.** Fix the issues above and try again.")
        
        # Enhanced error analysis
        if "duplicate" in message.lower():
            st.info("💡 **Duplicate Error:** This roll number or email might already be registered.")
            if st.button("🔍 Check Existing Students"):
                st.session_state.current_tab = 1  # Switch to manage students tab
                st.rerun()
        
        # Show troubleshooting based on debug mode
        if debug_mode:
            with st.expander("🔧 Advanced Troubleshooting", expanded=True):
                st.markdown("""
                **Detailed troubleshooting steps:**
                
                ### 📸 Image Quality Issues
                - **Resolution:** Use images with at least 640x480 resolution
                - **Lighting:** Ensure good, even lighting on the face
                - **Focus:** Use sharp, non-blurry images
                - **File size:** Keep images under 10MB but above 100KB
                - **Format:** Use JPG, JPEG, or PNG formats
                
                ### 👤 Face Detection Issues
                - **Single person:** Only one person should be visible per image
                - **Face visibility:** Entire face should be visible and facing camera
                - **Obstructions:** Remove glasses, masks, or hats if possible
                - **Angle:** Use frontal or slightly angled face shots
                
                ### 🔧 Technical Issues
                - **Duplicate data:** Check if roll number or email already exists
                - **File corruption:** Try re-uploading the images
                - **Memory issues:** Close other applications to free up memory
                - **Model loading:** Restart the application if this is the first use
                
                ### 🗃️ Database Issues
                - **Connection:** Check database connection
                - **Permissions:** Ensure write permissions to database
                - **Disk space:** Check available disk space
                """)
        else:
            with st.expander("🔧 Quick Troubleshooting"):
                st.markdown("""
                **Common solutions:**
                
                ✅ **Check for duplicates:** Roll number and email must be unique  
                ✅ **Improve photo quality:** Use well-lit, clear photos  
                ✅ **Verify face visibility:** Ensure faces are clearly visible  
                ✅ **Try different photos:** Use different angles or lighting  
                ✅ **Check file formats:** Use JPG, JPEG, or PNG files  
                ✅ **Restart if needed:** Close and reopen the application  
                
                **Still having issues?** Enable debug mode above for detailed analysis.
                """)
    
    def _render_manage_students_tab(self):
        """Render manage students tab with enhanced functionality"""
        st.markdown("### 📋 Current Students")
        
        try:
            # Get students list with error handling
            students = self._get_students_safely()
            
            if students:
                # Enhanced search functionality
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    search_term = st.text_input(
                        "🔍 Search students", 
                        placeholder="Enter name, roll number, email, or course",
                        help="Search across all student fields"
                    )
                
                with col2:
                    sort_by = st.selectbox(
                        "Sort by",
                        options=["name", "roll_number", "course", "created_at"],
                        help="Sort students by field"
                    )
                
                # Filter and sort students
                filtered_students = self._filter_and_sort_students(students, search_term, sort_by)
                
                if filtered_students:
                    # Display students table with enhanced formatting
                    self._display_enhanced_students_table(filtered_students)
                    
                    # Show statistics
                    self._display_student_statistics(students, filtered_students)
                    
                    # Student management actions
                    self._render_student_management_actions(students)
                else:
                    st.info(f"No students found matching '{search_term}'")
                    
            else:
                self._render_no_students_message()
                
        except Exception as e:
            logger.error(f"Error in student management tab: {e}")
            st.error(f"❌ Error loading students: {str(e)}")
            
            # Fallback option
            if st.button("🔄 Retry Loading Students"):
                st.rerun()
    
    def _get_students_safely(self) -> List[Dict]:
        """Get students list with multiple fallback methods"""
        try:
            if self.student_service:
                return self.student_service.get_all_students()
        except Exception as e:
            logger.warning(f"Service failed, trying direct database: {e}")
        
        try:
            from db import get_all_students
            return get_all_students()
        except Exception as e:
            logger.error(f"Direct database also failed: {e}")
            return []
    
    def _filter_and_sort_students(self, students: List[Dict], search_term: str, sort_by: str) -> List[Dict]:
        """Filter and sort students based on search term and sort criteria"""
        # Filter students
        if search_term:
            search_lower = search_term.lower()
            filtered_students = [
                s for s in students if
                search_lower in s.get('name', '').lower() or
                search_lower in s.get('roll_number', '').lower() or
                search_lower in s.get('email', '').lower() or
                search_lower in s.get('course', '').lower()
            ]
        else:
            filtered_students = students
        
        # Sort students
        try:
            if sort_by == "created_at":
                # Sort by creation date (newest first)
                filtered_students.sort(key=lambda x: x.get(sort_by, ''), reverse=True)
            else:
                # Sort alphabetically
                filtered_students.sort(key=lambda x: x.get(sort_by, '').lower())
        except Exception as e:
            logger.warning(f"Sorting failed: {e}")
        
        return filtered_students
    
    def _display_enhanced_students_table(self, students: List[Dict]):
        """Display students in an enhanced formatted table"""
        df = pd.DataFrame(students)
        
        # Select and order columns for display
        display_columns = []
        column_config = {}
        
        # Add columns that exist in the data
        if 'name' in df.columns:
            display_columns.append('name')
            column_config['name'] = "👤 Student Name"
            
        if 'roll_number' in df.columns:
            display_columns.append('roll_number')
            column_config['roll_number'] = "🎫 Roll Number"
            
        if 'email' in df.columns:
            display_columns.append('email')
            column_config['email'] = "📧 Email"
            
        if 'course' in df.columns:
            display_columns.append('course')
            column_config['course'] = "📚 Course"
            
        if 'phone' in df.columns:
            display_columns.append('phone')
            column_config['phone'] = "📱 Phone"
            
        if 'photo_count' in df.columns:
            display_columns.append('photo_count')
            column_config['photo_count'] = st.column_config.NumberColumn(
                "📸 Photos",
                format="%d"
            )
            
        if 'created_at' in df.columns:
            display_columns.append('created_at')
            column_config['created_at'] = "📅 Registered"
        
        # Display the enhanced table
        if display_columns:
            st.dataframe(
                df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )
        else:
            # Fallback - show all columns
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    def _display_student_statistics(self, all_students: List[Dict], filtered_students: List[Dict]):
        """Display comprehensive student statistics"""
        st.markdown("#### 📊 Statistics")
        
        # Create statistics
        total_students = len(all_students)
        filtered_count = len(filtered_students)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Students", total_students)
        
        with col2:
            st.metric("📝 Filtered Results", filtered_count)
        
        with col3:
            if all_students and 'course' in pd.DataFrame(all_students).columns:
                courses_df = pd.DataFrame(all_students)
                unique_courses = courses_df['course'].nunique()
                st.metric("📚 Courses", unique_courses)
            else:
                st.metric("📚 Courses", "N/A")
        
        with col4:
            if all_students and 'photo_count' in pd.DataFrame(all_students).columns:
                photos_df = pd.DataFrame(all_students)
                avg_photos = photos_df['photo_count'].mean()
                st.metric("📸 Avg Photos", f"{avg_photos:.1f}")
            else:
                st.metric("📸 Status", "Active")
        
        # Course distribution chart
        if len(all_students) > 0:
            try:
                df = pd.DataFrame(all_students)
                if 'course' in df.columns:
                    course_counts = df['course'].value_counts()
                    
                    if len(course_counts) > 1:
                        with st.expander("📊 Course Distribution", expanded=False):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.bar_chart(course_counts)
                            
                            with col2:
                                for course, count in course_counts.items():
                                    percentage = (count / total_students) * 100
                                    st.metric(course, f"{count} ({percentage:.1f}%)")
            except Exception as e:
                logger.warning(f"Could not generate course distribution: {e}")
    
    def _render_student_management_actions(self, students: List[Dict]):
        """Render student management actions"""
        st.markdown("---")
        st.markdown("### 🛠️ Student Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🗑️ Remove Student")
            
            if students:
                student_options = [""] + [
                    f"{s.get('name', 'Unknown')} ({s.get('roll_number', 'N/A')}) - {s.get('course', 'Unknown')}" 
                    for s in students
                ]
                
                student_to_delete = st.selectbox(
                    "Select student to remove:", 
                    options=student_options,
                    help="Select a student to remove from the system"
                )
                
                if student_to_delete:
                    if st.button("🗑️ Remove Student", type="secondary"):
                        self._handle_student_deletion(student_to_delete)
            else:
                st.info("No students available to remove")
        
        with col2:
            st.markdown("#### 📊 Export Data")
            
            if students:
                # Export options
                export_format = st.selectbox(
                    "Export format:",
                    options=["CSV", "Excel"],
                    help="Choose export format"
                )
                
                if st.button("📥 Export Students", type="secondary"):
                    self._handle_student_export(students, export_format)
            else:
                st.info("No students available to export")
    
    def _handle_student_deletion(self, student_selection: str):
        """Handle student deletion with confirmation"""
        try:
            # Extract student information
            roll_number = student_selection.split("(")[1].split(")")[0]
            student_name = student_selection.split(" (")[0]
            
            # Create confirmation key
            confirm_key = f"confirm_delete_{roll_number.replace(' ', '_').replace('.', '_')}"
            
            if st.session_state.get(confirm_key):
                # Perform deletion
                try:
                    success, message = self._delete_student_safely(roll_number)
                    
                    if success:
                        st.success(f"✅ {student_name} removed successfully!")
                        st.balloons()
                        
                        # Clear confirmation state
                        st.session_state[confirm_key] = False
                        
                        # Wait and refresh
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ Error removing student: {message}")
                        st.session_state[confirm_key] = False
                        
                except Exception as e:
                    st.error(f"❌ Error deleting student: {str(e)}")
                    st.session_state[confirm_key] = False
            else:
                # Request confirmation
                st.session_state[confirm_key] = True
                st.warning(f"⚠️ Click 'Remove Student' again to confirm deletion of **{student_name}**")
                st.warning("⚠️ This action cannot be undone!")
                
        except Exception as e:
            logger.error(f"Error in student deletion: {e}")
            st.error(f"❌ Error processing deletion: {str(e)}")
    
    def _delete_student_safely(self, roll_number: str) -> tuple:
        """Delete student with multiple fallback methods"""
        try:
            if self.student_service:
                return self.student_service.delete_student_by_roll(roll_number)
        except Exception as e:
            logger.warning(f"Service deletion failed, trying direct: {e}")
        
        try:
            from db import delete_student
            success = delete_student(roll_number)
            message = "Student deleted successfully" if success else "Failed to delete student"
            return success, message
        except Exception as e:
            logger.error(f"Direct deletion failed: {e}")
            return False, str(e)
    
    def _handle_student_export(self, students: List[Dict], format_type: str):
        """Handle student data export"""
        try:
            df = pd.DataFrame(students)
            
            if format_type == "CSV":
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"students_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            elif format_type == "Excel":
                # For Excel export (requires openpyxl)
                try:
                    excel_data = df.to_excel(index=False)
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_data,
                        file_name=f"students_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception:
                    st.error("Excel export requires openpyxl. Falling back to CSV.")
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV (Fallback)",
                        data=csv_data,
                        file_name=f"students_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            st.success(f"✅ Export prepared! Click the download button above.")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            st.error(f"❌ Export failed: {str(e)}")
    
    def _render_no_students_message(self):
        """Render enhanced message when no students are registered"""
        st.info("📝 No students registered yet. Get started by adding your first student!")
        
        # Create attractive getting started guide
        with st.expander("🚀 Getting Started Guide", expanded=True):
            st.markdown("""
            ### 📋 **Step-by-Step Registration Process:**
            
            1. **📝 Fill Student Information**
               - Enter full name, roll number, and email
               - Select the appropriate course/department  
               - Add phone number (optional)
            
            2. **📸 Upload Face Photos**
               - Upload 2-5 clear photos of the student
               - Use good lighting and different angles
               - Ensure the face is clearly visible
            
            3. **🔍 Enable Debug Mode** (recommended for first-time)
               - Get detailed feedback during processing
               - See exactly what happens with each photo
               - Troubleshoot any issues immediately
            
            4. **🎓 Register Student**
               - Click the registration button
               - Wait for processing to complete
               - Form will clear automatically after success
            
            ### 💡 **Pro Tips for Best Results:**
            
            ✅ **Photo Quality:** Use well-lit, high-resolution images  
            ✅ **Face Visibility:** Ensure entire face is visible and unobstructed  
            ✅ **Multiple Angles:** Include frontal view and slight side angles  
            ✅ **Unique Data:** Each roll number and email must be unique  
            ✅ **Supported Formats:** JPG, JPEG, PNG files work best  
            ✅ **File Size:** Keep images between 100KB - 10MB  
            
            ### 🔧 **Troubleshooting:**
            
            - **Enable debug mode** for detailed processing information
            - **Check image quality** if face detection fails  
            - **Verify uniqueness** of roll numbers and emails
            - **Restart application** if experiencing issues
            """)
        
        # Quick start button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🎯 Ready to Get Started?")
            st.info("👆 Use the **'Add Student'** tab above to register your first student!")
