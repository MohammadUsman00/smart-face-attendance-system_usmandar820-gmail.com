import os
import time
import uuid
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px
import cv2
import numpy as np

# Import our fixed modules  
from db import init_database, add_student_with_photos, get_all_students, delete_student, recognize_student, mark_attendance, get_attendance_records, get_today_stats, get_attendance_analytics, delete_all_students, delete_all_users_except_admin
from auth import signup_user, login_user, get_all_users, delete_user, initiate_password_reset, reset_password
import face_utils as fu

# Load environment variables
load_dotenv()

# Streamlit configuration
st.set_page_config(
    page_title="🎓 Smart Face Attendance System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open("style.css", "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS file not found. Using default styling.")

load_css()


# Initialize session state
def init_session_state():
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'

def login_page():
    st.title("🎓 Smart Face Attendance System")
    st.markdown("### 🔐 Secure Authentication Portal")
    
    # Create tabs for login, signup, and forgot password
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "👤 Sign Up", "🔒 Forgot Password"])
    
    with tab1:
        st.markdown("#### Welcome Back!")
        with st.form("login_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                email = st.text_input("📧 Email", placeholder="Enter your email")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            with col_btn2:
                st.form_submit_button("👤 Demo Login", use_container_width=True, type="secondary", 
                                    help="Use signup using your email and password")
            
            if login_btn:
                if email and password:
                    success, message, user_data = login_user(email, password)
                    if success:
                        st.session_state.user_authenticated = True
                        st.session_state.user_email = email
                        st.session_state.user_role = user_data.get('role', 'user')
                        st.success("🎉 Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("⚠️ Please fill in all fields")
        
        # Demo credentials info
        st.info("🔑 **Demo Credentials:**\n- email: youremail@gmail.com / password:yourpassword")
    
    with tab2:
        st.markdown("#### Create New Account")
        with st.form("signup_form"):
            email = st.text_input("📧 Email", placeholder="Enter your email", key="signup_email")
            password = st.text_input("🔒 Password", type="password", placeholder="Create password", key="signup_password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm password")
            
            signup_btn = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if signup_btn:
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        success, message, _ = signup_user(email, password)
                        if success:
                            st.success(f"✅ {message}. You can now login!")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("⚠️ Please fill in all fields")
    
    with tab3:
        st.markdown("#### Reset Your Password")
        show_forgot_password_form()

def show_forgot_password_form():
    """Enhanced forgot password with better UX"""
    st.info("💡 Enter your email to receive password reset instructions")
    
    with st.form("forgot_password_form"):
        email = st.text_input("📧 Email Address", placeholder="Enter your registered email")
        reset_btn = st.form_submit_button("📤 Send Reset Link", use_container_width=True)
        
        if reset_btn:
            if email:
                success, message, token = initiate_password_reset(email)
                if success and token:
                    st.success("✅ Password reset token generated!")
                    st.warning("🔧 **Demo Mode**: Copy this token to reset your password")
                    st.code(f"{token}", language="text")
                    
                    # Store in session for password reset form
                    st.session_state.reset_token = token
                    st.session_state.reset_email = email
                    st.session_state.show_password_reset = True
                elif success:
                    st.success("✅ If the email exists, reset instructions have been sent")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("⚠️ Please enter your email address")
    
    # Show password reset form if token is available
    if st.session_state.get('show_password_reset', False):
        show_password_reset_form()

def show_password_reset_form():
    """Password reset form using token"""
    st.markdown("---")
    st.markdown("#### 🔄 Set New Password")
    
    with st.form("password_reset_form"):
        st.info(f"🔐 Resetting password for: **{st.session_state.get('reset_email', '')}**")
        
        reset_token = st.text_input("🎫 Reset Token", 
                                   value=st.session_state.get('reset_token', ''),
                                   help="Paste the reset token from above")
        new_password = st.text_input("🔒 New Password", type="password", 
                                   placeholder="Enter new password (min 6 characters)")
        confirm_new_password = st.text_input("🔒 Confirm New Password", type="password", 
                                           placeholder="Confirm new password")
        
        col1, col2 = st.columns(2)
        with col1:
            reset_password_btn = st.form_submit_button("🔄 Reset Password", use_container_width=True)
        with col2:
            cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True, type="secondary")
        
        if reset_password_btn:
            if reset_token and new_password and confirm_new_password:
                if new_password != confirm_new_password:
                    st.error("❌ Passwords do not match")
                else:
                    success, message = reset_password(st.session_state.get('reset_email', ''),
                                                    reset_token, new_password)
                    if success:
                        st.success("✅ Password reset successful! You can now login.")
                        st.balloons()
                        # Clear reset session data
                        for key in ['reset_token', 'reset_email', 'show_password_reset']:
                            st.session_state.pop(key, None)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error("⚠️ Please fill in all fields")
        
        if cancel_btn:
            for key in ['reset_token', 'reset_email', 'show_password_reset']:
                st.session_state.pop(key, None)
            st.rerun()

def admin_dashboard():
    st.title("📊 Admin Dashboard")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🎯 Admin Control Panel")
        
        # Navigation buttons
        if st.button("📈 Dashboard Overview", use_container_width=True):
            st.session_state.current_page = "Dashboard Overview"
        if st.button("👥 Student Management", use_container_width=True):
            st.session_state.current_page = "Student Management" 
        if st.button("📷 Mark Attendance", use_container_width=True):
            st.session_state.current_page = "Mark Attendance"
        if st.button("📝 Attendance Records", use_container_width=True):
            st.session_state.current_page = "Attendance Records"
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
        if st.button("👤 User Management", use_container_width=True):
            st.session_state.current_page = "User Management"
        if st.button("⚠️ Danger Zone", use_container_width=True):
            st.session_state.current_page = "Danger Zone"
        
        st.markdown("---")
        st.markdown(f"**Logged in as:** {st.session_state.user_email}")
        st.markdown(f"**Role:** Admin")
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
    
    # Show current page
    current_page = st.session_state.get('current_page', 'Dashboard Overview')
    
    if current_page == "Dashboard Overview":
        show_dashboard_overview()
    elif current_page == "Student Management":
        show_student_management()
    elif current_page == "Mark Attendance":
        show_mark_attendance()
    elif current_page == "Attendance Records":
        show_attendance_records()
    elif current_page == "Analytics":
        show_analytics()
    elif current_page == "User Management":
        show_user_management()
    elif current_page == "Danger Zone":
        show_danger_zone()

def user_dashboard():
    st.title("🎓 Student Dashboard")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🎯 Student Panel")
        
        if st.button("📈 My Dashboard", use_container_width=True):
            st.session_state.current_page = "User Dashboard"
        if st.button("📷 Mark Attendance", use_container_width=True):
            st.session_state.current_page = "Mark Attendance"
        
        st.markdown("---")
        st.markdown(f"**Logged in as:** {st.session_state.user_email}")
        st.markdown(f"**Role:** Student")
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
    
    # Show current page
    current_page = st.session_state.get('current_page', 'User Dashboard')
    
    if current_page == "User Dashboard":
        show_user_dashboard_content()
    elif current_page == "Mark Attendance":
        show_mark_attendance()

def show_user_dashboard_content():
    """User dashboard content"""
    st.markdown("## 📊 Today's Overview")
    
    try:
        stats = get_today_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Total Students", stats.get('total_students', 0))
        with col2:
            st.metric("✅ Present Today", stats.get('present_today', 0))
        with col3:
            st.metric("❌ Absent Today", stats.get('absent_today', 0))
        with col4:
            attendance_rate = stats.get('attendance_rate', 0)
            st.metric("📊 Attendance Rate", f"{attendance_rate:.1f}%")
        
        # Recent attendance
        st.markdown("### 🕐 Recent Attendance")
        recent_records = get_attendance_records(date.today(), date.today())
        if recent_records:
            recent_df = pd.DataFrame(recent_records[-10:])
            st.dataframe(
                recent_df[['name', 'roll_number', 'time_in', 'time_out']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No attendance records today yet")
            
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")

def show_mark_attendance():
    """Enhanced attendance marking with IN/OUT detection"""
    st.markdown("## 📷 Smart Attendance System")
    st.markdown("**Dual Mode Tracking: Entry & Exit**")
    
    # Instructions
    with st.expander("📋 How to Use", expanded=False):
        st.markdown("""
        **For best results:**
        - ✅ Ensure good lighting
        - ✅ Look directly at the camera
        - ✅ Keep your face clearly visible
        - ✅ Remove any obstructions (mask, hand, etc.)
        - ✅ Stay still when taking the photo
        
        **System automatically detects:**
        - 🟢 **IN** - When entering college
        - 🔴 **OUT** - When leaving college
        """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Camera input
        camera_input = st.camera_input("📸 Take picture for attendance")
        
        if camera_input is not None:
            # Process the image
            file_bytes = np.asarray(bytearray(camera_input.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            with st.spinner("🔍 Processing face recognition..."):
                try:
                    # Recognize student
                    recognition_result = recognize_student(img)
                    
                    if recognition_result['success']:
                        student_info = recognition_result['student']
                        confidence = recognition_result['confidence']
                        
                        # Show recognition result
                        st.success(f"👋 Welcome, **{student_info['name']}**!")
                        
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.info(f"🎫 Roll: {student_info['roll_number']}")
                            st.info(f"📚 Course: {student_info.get('course', 'N/A')}")
                        with col_info2:
                            st.info(f"📊 Confidence: {confidence:.1f}%")
                            
                            # Determine IN/OUT automatically
                            today_status = get_attendance_records(date.today(), date.today())
                            student_today = [r for r in today_status if r['student_id'] == student_info['id']]
                            
                            if not student_today:
                                action = "IN"
                                st.success("🟢 **Action:** ENTRY (IN)")
                            elif student_today[0].get('time_out') is None:
                                action = "OUT" 
                                st.warning("🔴 **Action:** EXIT (OUT)")
                            else:
                                action = "IN"
                                st.info("🟡 **Action:** RE-ENTRY (IN)")
                        
                        # Mark attendance
                        attendance_result = mark_attendance(student_info['id'], action)
                        
                        if attendance_result['success']:
                            st.success(f"✅ Attendance marked: **{action}** at {datetime.now().strftime('%I:%M:%S %p')}")
                            st.balloons()
                            
                            # Show today's complete status
                            updated_records = get_attendance_records(date.today(), date.today())
                            student_record = [r for r in updated_records if r['student_id'] == student_info['id']]
                            if student_record:
                                record = student_record[0]
                                st.markdown("#### 📊 Today's Status")
                                status_col1, status_col2 = st.columns(2)
                                with status_col1:
                                    in_time = record.get('time_in', 'Not marked')
                                    st.metric("🟢 Entry Time", in_time if in_time else "Not marked")
                                with status_col2:
                                    out_time = record.get('time_out', 'Not marked')
                                    st.metric("🔴 Exit Time", out_time if out_time else "Not marked")
                        else:
                            st.warning(f"⚠️ {attendance_result['message']}")
                            
                    else:
                        st.error("❌ Face not recognized")
                        st.info("💡 **Troubleshooting:**\n- Ensure good lighting\n- Look directly at camera\n- Remove any face coverings\n- Try repositioning yourself")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col2:
        # Today's summary
        st.markdown("### 📊 Today's Summary")
        try:
            stats = get_today_stats()
            st.metric("👥 Total", stats.get('total_students', 0))
            st.metric("✅ Present", stats.get('present_today', 0))
            st.metric("📈 Rate", f"{stats.get('attendance_rate', 0):.1f}%")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

def show_dashboard_overview():
    """Enhanced dashboard with real-time stats"""
    st.markdown("## 📈 Dashboard Overview")
    
    try:
        stats = get_today_stats()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Students", stats.get('total_students', 0))
        with col2:
            st.metric("✅ Present Today", stats.get('present_today', 0))
        with col3:
            st.metric("❌ Absent Today", stats.get('absent_today', 0))
        with col4:
            attendance_rate = stats.get('attendance_rate', 0)
            st.metric("📊 Attendance Rate", f"{attendance_rate:.1f}%")
        
        st.markdown("---")
        
        # Today's activity
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 Today's Attendance")
            today_records = get_attendance_records(date.today(), date.today())
            if today_records:
                df = pd.DataFrame(today_records)
                st.dataframe(
                    df[['name', 'roll_number', 'time_in', 'time_out']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No attendance records for today yet")
        
        with col2:
            st.markdown("### 🎯 Quick Actions")
            if st.button("➕ Add New Student", use_container_width=True):
                st.session_state.current_page = "Student Management"
                st.rerun()
            if st.button("📝 View All Records", use_container_width=True):
                st.session_state.current_page = "Attendance Records" 
                st.rerun()
            if st.button("📊 View Analytics", use_container_width=True):
                st.session_state.current_page = "Analytics"
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")

def show_student_management():
    """Enhanced student management with course dropdown and proper feedback"""
    st.markdown("## 👥 Student Management")
    
    tab1, tab2 = st.tabs(["➕ Add Student", "📋 Manage Students"])
    
    with tab1:
        st.markdown("### 📸 Register New Student")
        
        # Form with proper error handling and success feedback
        with st.form("add_student_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("👤 Full Name *", placeholder="Enter student name")
                roll_number = st.text_input("🎫 Roll Number *", placeholder="Enter roll number")
                email = st.text_input("📧 Email *", placeholder="Enter email address")
            with col2:
                phone = st.text_input("📱 Phone", placeholder="Enter phone number")
                
                # Enhanced course selection with proper options
                course_options = {
                    "CSE": "Computer Science Engineering 💻",
                    "CE": "Civil Engineering 🏗️", 
                    "EE": "Electrical Engineering ⚡",
                    "BE": "Biomedical Engineering 🧬 ",
                    "ME": "Mechanical Engineering ⚙️"
                }
                
                course = st.selectbox("📚 Course *", 
                                    options=list(course_options.keys()),
                                    format_func=lambda x: course_options[x])
            
            st.markdown("**📸 Upload Student Photos (2-5 images for best accuracy)**")
            st.info("💡 **Tips for better recognition:**\n- Use different angles and lighting\n- Include photos with/without glasses\n- Ensure clear face visibility\n- Good lighting is essential")
            
            uploaded_files = st.file_uploader(
                "Choose images", 
                type=['jpg', 'jpeg', 'png'], 
                accept_multiple_files=True,
                help="Upload 2-5 clear photos from different angles"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} image(s) uploaded")
                
                # Show preview with checkbox
                show_preview = st.checkbox("👁️ Preview Images")
                if show_preview:
                    cols = st.columns(min(len(uploaded_files), 5))
                    for i, file in enumerate(uploaded_files[:5]):
                        with cols[i]:
                            st.image(file, caption=f"Photo {i+1}",  use_container_width=True)
            
            # Submit button
            submit_button = st.form_submit_button("✨ Register Student", use_container_width=True)
            
            # Handle form submission with proper error handling
            if submit_button:
                # Validate required fields
                if not name or not roll_number or not email:
                    st.error("⚠️ Please fill all required fields (*)")
                elif not uploaded_files:
                    st.error("⚠️ Please upload at least one photo")
                elif len(uploaded_files) < 2:
                    st.warning("⚠️ For better accuracy, please upload at least 2 photos")
                elif len(uploaded_files) > 5:
                    st.error("⚠️ Maximum 5 photos allowed")
                else:
                    # Process registration with detailed feedback
                    with st.spinner("🔄 Processing photos and creating student profile..."):
                        try:
                            # Process images
                            image_data = []
                            processed_count = 0
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, uploaded_file in enumerate(uploaded_files):
                                status_text.text(f"Processing image {i+1}/{len(uploaded_files)}...")
                                progress_bar.progress((i + 1) / len(uploaded_files))
                                
                                try:
                                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                                    img = cv2.imdecode(file_bytes, 1)
                                    
                                    if img is not None:
                                        image_data.append(img)
                                        processed_count += 1
                                    else:
                                        st.warning(f"⚠️ Could not process image {i+1}")
                                except Exception as e:
                                    st.warning(f"⚠️ Error processing image {i+1}: {str(e)}")
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if processed_count == 0:
                                st.error("❌ No valid images could be processed")
                            else:
                                # Add student to database
                                success, message = add_student_with_photos(
                                    name=name.strip(),
                                    roll_number=roll_number.strip(),
                                    email=email.strip().lower(),
                                    phone=phone.strip() if phone else None,
                                    course=course,
                                    images=image_data
                                )
                                
                                if success:
                                    # SUCCESS - Show balloons and detailed feedback
                                    st.success("🎉 Student registered successfully!")
                                    st.balloons()
                                    
                                    # Show registration summary
                                    st.markdown("#### 📊 Registration Summary")
                                    summary_col1, summary_col2 = st.columns(2)
                                    
                                    with summary_col1:
                                        st.info(f"**👤 Name:** {name}")
                                        st.info(f"**🎫 Roll Number:** {roll_number}")
                                        st.info(f"**📧 Email:** {email}")
                                    
                                    with summary_col2:
                                        st.info(f"**📚 Course:** {course_options[course]}")
                                        st.info(f"**📸 Photos Processed:** {processed_count}")
                                        st.info(f"**✅ Status:** Active")
                                    
                                    st.success(f"✨ **{name}** has been successfully registered!")
                                    
                                    # Auto-refresh after 3 seconds
                                    time.sleep(3)
                                    st.rerun()
                                    
                                else:
                                    # ERROR - Show detailed error message
                                    st.error(f"❌ Registration failed: {message}")
                                    
                                    # Show troubleshooting tips
                                    with st.expander("🔧 Troubleshooting Tips"):
                                        st.markdown("""
                                        **Common issues:**
                                        - **Duplicate roll number:** Each student needs a unique roll number
                                        - **Duplicate email:** Each email can only be used once
                                        - **No face detected:** Ensure photos show clear faces
                                        - **Poor image quality:** Use well-lit, clear photos
                                        
                                        **Solutions:**
                                        - Check if student is already registered
                                        - Use a different email address
                                        - Upload clearer photos with better lighting
                                        - Make sure faces are clearly visible
                                        """)
                                        
                        except Exception as e:
                            st.error(f"❌ Unexpected error during registration: {str(e)}")
                            logger.error(f"Student registration error: {e}")
                            
                            # Show debug info in expander
                            with st.expander("🔧 Debug Information"):
                                st.code(f"Error details: {str(e)}")
                                st.text("Please try again or contact support if the problem persists.")
    
    with tab2:
        st.markdown("### 📋 Current Students")
        
        try:
            students = get_all_students()
            if students:
                # Create enhanced DataFrame
                students_df = pd.DataFrame(students)
                
                # Display with better formatting
                st.dataframe(
                    students_df[['name', 'roll_number', 'email', 'course', 'created_at']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "name": "Student Name",
                        "roll_number": "Roll Number",
                        "email": "Email Address", 
                        "course": "Course",
                        "created_at": "Registration Date"
                    }
                )
                
                # Show statistics
                st.markdown("#### 📊 Statistics")
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                
                with stat_col1:
                    st.metric("👥 Total Students", len(students))
                with stat_col2:
                    course_counts = students_df['course'].value_counts()
                    most_popular = course_counts.index[0] if len(course_counts) > 0 else "N/A"
                    st.metric("📚 Most Popular Course", most_popular)
                with stat_col3:
                    # Calculate average photos per student (if photo_count exists)
                    if 'photo_count' in students_df.columns:
                        avg_photos = students_df['photo_count'].mean()
                        st.metric("📸 Avg Photos/Student", f"{avg_photos:.1f}")
                    else:
                        st.metric("📅 Latest Registration", "Today")
                
                st.markdown("---")
                st.markdown("### 🗑️ Remove Student")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    student_options = [""] + [f"{s['name']} ({s['roll_number']}) - {s['course']}" for s in students]
                    student_to_delete = st.selectbox("Select student to remove:", options=student_options)
                
                with col2:
                    if student_to_delete:
                        if st.button("🗑️ Remove", type="secondary"):
                            # Get roll number from selection
                            roll_number = student_to_delete.split("(")[1].split(")")[0]
                            confirm_key = f"confirm_delete_{roll_number}"
                            
                            if st.session_state.get(confirm_key) == roll_number:
                                success, message = delete_student(roll_number)
                                if success:
                                    st.success("✅ Student removed successfully!")
                                    st.balloons()
                                    st.session_state[confirm_key] = None
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error removing student: {message}")
                            else:
                                st.session_state[confirm_key] = roll_number
                                st.warning("⚠️ Click 'Remove' again to confirm deletion")
            else:
                st.info("📝 No students registered yet. Use the 'Add Student' tab to get started!")
                
                # Show getting started guide
                with st.expander("🚀 Getting Started Guide"):
                    st.markdown("""
                    **How to add your first student:**
                    1. Click on the **'Add Student'** tab above
                    2. Fill in all required fields (marked with *)
                    3. Upload 2-5 clear photos of the student
                    4. Click **'Register Student'** 
                    5. Wait for processing and confirmation
                    
                    **Tips for success:**
                    - Use good lighting for photos
                    - Include different angles
                    - Ensure faces are clearly visible
                    - Each student needs unique roll number and email
                    """)
                
        except Exception as e:
            st.error(f"❌ Error loading students: {str(e)}")
            logger.error(f"Error in student management: {e}")


def show_attendance_records():
    """Enhanced attendance records with filtering"""
    st.markdown("## 📝 Attendance Records")
    
    # Enhanced filtering
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input("📅 Start Date", value=date.today() - timedelta(days=7))
    with col2:
        end_date = st.date_input("📅 End Date", value=date.today())
    with col3:
        st.write("")  # Spacing
        load_btn = st.button("🔍 Load Records", use_container_width=True)
    
    if load_btn:
        try:
            with st.spinner("📊 Loading attendance records..."):
                records = get_attendance_records(start_date, end_date)
                
            if records:
                records_df = pd.DataFrame(records)
                
                # Enhanced summary
                st.markdown("### 📊 Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📝 Total Records", len(records_df))
                with col2:
                    unique_students = records_df['roll_number'].nunique()
                    st.metric("👥 Students", unique_students)
                with col3:
                    unique_dates = records_df['date'].nunique()
                    st.metric("📅 Days", unique_dates)
                with col4:
                    # Count complete attendance (both IN and OUT)
                    complete_attendance = len(records_df.dropna(subset=['time_in', 'time_out']))
                    st.metric("✅ Complete", complete_attendance)
                
                st.markdown("---")
                
                # Enhanced records table
                st.markdown("### 📋 Detailed Records")
                
                # Add status column
                def get_status(row):
                    if row['time_in'] and row['time_out']:
                        return "✅ Complete"
                    elif row['time_in']:
                        return "🟡 In Progress"
                    else:
                        return "❌ Incomplete"
                
                records_df['Status'] = records_df.apply(get_status, axis=1)
                
                st.dataframe(
                    records_df[['name', 'roll_number', 'date', 'time_in', 'time_out', 'Status']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "name": "Student Name",
                        "roll_number": "Roll Number",
                        "date": "Date",
                        "time_in": "Entry Time",
                        "time_out": "Exit Time",
                        "Status": "Status"
                    }
                )
                
                # Download options
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = records_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"attendance_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Create summary report
                    summary_data = {
                        'Metric': ['Total Records', 'Unique Students', 'Date Range', 'Complete Attendance', 'In Progress', 'Average Daily Attendance'],
                        'Value': [
                            len(records_df),
                            records_df['roll_number'].nunique(), 
                            f"{start_date} to {end_date}",
                            (records_df['Status'] == '✅ Complete').sum(),
                            (records_df['Status'] == '🟡 In Progress').sum(),
                            f"{len(records_df) / unique_dates:.1f}" if unique_dates > 0 else "0"
                        ]
                    }
                    summary_csv = pd.DataFrame(summary_data).to_csv(index=False)
                    st.download_button(
                        label="📊 Download Summary",
                        data=summary_csv,
                        file_name=f"attendance_summary_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
            else:
                st.info(f"📝 No attendance records found for {start_date} to {end_date}")
                
        except Exception as e:
            st.error(f"❌ Error loading records: {str(e)}")

def show_analytics():
    """Enhanced analytics with course-wise breakdown and accurate attendance %"""
    st.markdown("## 📊 Advanced Analytics Dashboard")
    
    try:
        with st.spinner("📈 Generating analytics..."):
            analytics_data = get_attendance_analytics()
      
            if analytics_data:
    # Daily attendance trend
               if analytics_data.get('daily_attendance'):
                  st.markdown("### 📊 Daily Attendance (Bar)")
        daily_df = pd.DataFrame(analytics_data['daily_attendance'])
        if not daily_df.empty:
            # optional: ensure proper ordering if 'date' is string
            # daily_df['date'] = pd.to_datetime(daily_df['date'])
            # daily_df = daily_df.sort_values('date')

            fig = px.bar(
                daily_df,
                x='date',
                y='count',
                title='Students Present by Day',
                labels={'count': 'Students Present', 'date': 'Date'},
                text='count'  # shows values on bars; remove if not needed
            )
            fig.update_traces(textposition='outside', marker_line_width=0.5)
            fig.update_layout(height=400, xaxis_tickangle=45, uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)

            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if analytics_data.get('course_attendance'):
                    st.markdown("### 📚 Course-wise Attendance")
                    course_df = pd.DataFrame(analytics_data['course_attendance'])
                    if not course_df.empty:
                        fig = px.pie(course_df, values='total_students', names='course',
                                     title='Student Distribution by Course')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("#### 🏆 Course Performance")
                        st.dataframe(
                            course_df[['course', 'total_students', 'present_records', 'total_classes', 'attendance_rate']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "course": "Course",
                                "total_students": "Total Students", 
                                "present_records": "Total Present Records",
                                "total_classes": "Total Classes",
                                "attendance_rate": st.column_config.NumberColumn("Attendance Rate (%)", format="%.1f%%")
                            }
                        )
            
            with col2:
                if analytics_data.get('student_attendance'):
                    st.markdown("### 👥 Top Performers")
                    student_df = pd.DataFrame(analytics_data['student_attendance'])
                    if not student_df.empty:
                        # already computed in backend; but defensively compute again using total_days
                        student_df['attendance_percentage'] = student_df.apply(
                            lambda r: round((r['present_days'] / r['total_days']) * 100, 1) if r['total_days'] > 0 else 0.0,
                            axis=1
                        ).clip(upper=100)

                        top_students = student_df.sort_values(by='attendance_percentage', ascending=False).head(10)
                        fig = px.bar(top_students, x='attendance_percentage', y='name',
                                     title='Top 10 Students by Attendance %', labels={'attendance_percentage': 'Attendance %', 'name': 'Student'},
                                     orientation='h', color='attendance_percentage', color_continuous_scale='Viridis')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("#### 📊 Attendance Distribution")
                        ranges = [
                            ('90-100%', ((student_df['attendance_percentage'] >= 90) & (student_df['attendance_percentage'] <= 100)).sum()),
                            ('75-89%', ((student_df['attendance_percentage'] >= 75) & (student_df['attendance_percentage'] < 90)).sum()),
                            ('60-74%', ((student_df['attendance_percentage'] >= 60) & (student_df['attendance_percentage'] < 75)).sum()),
                            ('Below 60%', (student_df['attendance_percentage'] < 60).sum())
                        ]
                        ranges_df = pd.DataFrame(ranges, columns=['Range', 'Students'])
                        ranges_df = ranges_df[ranges_df['Students'] > 0]
                        if not ranges_df.empty:
                            fig_ranges = px.bar(ranges_df, x='Range', y='Students', title='Students by Attendance Range',
                                               color='Students', color_continuous_scale='RdYlGn')
                            fig_ranges.update_layout(height=300)
                            st.plotly_chart(fig_ranges, use_container_width=True)
            
            # Detailed student statistics
            if analytics_data.get('student_attendance'):
                st.markdown("---")
                st.markdown("### 📊 Complete Student Statistics")
                student_df = pd.DataFrame(analytics_data['student_attendance'])
                st.dataframe(
                    student_df[['name', 'roll_number', 'present_days', 'total_days', 'attendance_percentage']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "name": "Student Name",
                        "roll_number": "Roll Number",
                        "present_days": "Days Present",
                        "total_days": "Total Classes",
                        "attendance_percentage": st.column_config.NumberColumn("Attendance %", format="%.1f%%")
                    }
                )
        else:
            st.info("📊 No analytics data available yet. Start by:")
            st.markdown("""
            1. **Add students** using Student Management
            2. **Mark attendance** for several days  
            3. **Return here** to view comprehensive analytics
            """)
            
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

def show_user_management():
    """Enhanced user management"""
    st.markdown("## 👤 User Management")
    
    try:
        users = get_all_users()
        if users:
            users_df = pd.DataFrame(users)
            
            st.markdown("### 👥 System Users")
            st.dataframe(
                users_df[['email', 'role', 'created_at']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "email": "Email Address",
                    "role": "Role",
                    "created_at": "Registration Date"
                }
            )
            
            # Add new admin user
            st.markdown("---")
            st.markdown("### ➕ Create Admin User")
            
            with st.form("add_admin_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_email = st.text_input("📧 Email", placeholder="admin@example.com")
                with col2:
                    new_password = st.text_input("🔒 Password", type="password", placeholder="Strong password")
                
                if st.form_submit_button("➕ Create Admin"):
                    if new_email and new_password:
                        success, message, _ = signup_user(new_email, new_password, role='admin')
                        if success:
                            st.success("✅ Admin user created successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("⚠️ Please fill all fields")
                        
        else:
            st.info("👤 No users found.")
            
    except Exception as e:
        st.error(f"❌ Error loading users: {str(e)}")

def show_danger_zone():
    """Enhanced danger zone with additional controls"""
    st.markdown("## ⚠️ Danger Zone")
    st.error("🚨 **WARNING:** These operations are irreversible!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗑️ Delete All Students")
        st.warning("This will permanently delete all student records and their photos")
        
        with st.form("delete_students_form"):
            confirm_students = st.checkbox("I understand this will delete ALL student data")
            confirm_text_students = st.text_input("Type 'DELETE STUDENTS' to confirm:")
            delete_students_btn = st.form_submit_button("🗑️ Delete All Students", type="secondary")
            
            if delete_students_btn:
                if confirm_students and confirm_text_students == "DELETE STUDENTS":
                    try:
                        delete_all_students()
                        st.success("✅ All student records deleted successfully")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("⚠️ Please confirm the deletion properly")
    
    with col2:
        st.markdown("### 👥 Delete All Users (Except Admin)")
        st.warning("This will permanently delete all user accounts except admins")
        
        with st.form("delete_users_form"):
            confirm_users = st.checkbox("I understand this will delete ALL non-admin users")
            confirm_text_users = st.text_input("Type 'DELETE USERS' to confirm:")
            delete_users_btn = st.form_submit_button("👥 Delete All Users", type="secondary")
            
            if delete_users_btn:
                if confirm_users and confirm_text_users == "DELETE USERS":
                    try:
                        delete_all_users_except_admin()
                        st.success("✅ All non-admin users deleted successfully")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("⚠️ Please confirm the deletion properly")
    
    # System reset option
    st.markdown("---")
    st.markdown("### 🔄 Complete System Reset")
    st.error("This will delete EVERYTHING and reset the system to initial state")
    
    with st.form("system_reset_form"):
        confirm_reset = st.checkbox("I want to completely reset the entire system")
        confirm_text_reset = st.text_input("Type 'RESET EVERYTHING' to confirm:")
        reset_btn = st.form_submit_button("💥 Complete Reset", type="secondary")
        
        if reset_btn:
            if confirm_reset and confirm_text_reset == "RESET EVERYTHING":
                try:
                    delete_all_students()
                    delete_all_users_except_admin()
                    st.success("✅ System completely reset!")
                    st.balloons()
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Reset failed: {str(e)}")
            else:
                st.error("⚠️ Please confirm the reset properly")

def logout():
    """Logout function"""
    for key in ['user_authenticated', 'user_email', 'user_role', 'current_page']:
        st.session_state.pop(key, None)
    st.rerun()

def main():
    # Initialize database and session
    init_database()
    init_session_state()
    
    if not st.session_state.user_authenticated:
        login_page()
    else:
        # Show appropriate dashboard based on role
        if st.session_state.user_role == 'admin':
            admin_dashboard()
        else:
            user_dashboard()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("Please ensure all dependencies are installed and configuration is correct.")
        
        # Debug information
        if st.checkbox("🔧 Show Debug Info"):
            st.exception(e)
