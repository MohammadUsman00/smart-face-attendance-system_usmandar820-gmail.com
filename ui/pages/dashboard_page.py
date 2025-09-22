"""
Main dashboard page component - Complete version
Extracted from app.py dashboard functionality
"""
import streamlit as st
import pandas as pd
import logging
import time
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from auth.session_manager import SessionManager
from services.attendance_service import AttendanceService
from services.student_service import StudentService
from ui.pages.student_management import StudentManagementPage
from ui.pages.attendance_page import AttendancePage
from ui.pages.analytics_page import AnalyticsPage

logger = logging.getLogger(__name__)

class DashboardPage:
    """Main dashboard page component with complete error handling"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        try:
            self.attendance_service = AttendanceService()
            self.student_service = StudentService()
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            self.attendance_service = None
            self.student_service = None
    
    def render(self):
        """Render appropriate dashboard based on user role"""
        current_user = self.session_manager.get_current_user()
        
        if not current_user:
            st.error("❌ Authentication error. Please login again.")
            self.session_manager.logout_user()
            st.rerun()
            return
        
        # Check session timeout
        if self.session_manager.check_session_timeout():
            st.warning("🕐 Session expired. Please login again.")
            st.rerun()
            return
        
        # Refresh session
        self.session_manager.refresh_session()
        
        # Render dashboard based on role
        if current_user['role'] == 'admin':
            self._render_admin_dashboard(current_user)
        else:
            self._render_user_dashboard(current_user)
    
    def _render_admin_dashboard(self, user: Dict):
        """Render admin dashboard"""
        st.title("📊 Admin Dashboard")
        
        # Sidebar navigation
        self._render_admin_sidebar(user)
        
        # Show current page based on session state
        current_page = st.session_state.get('current_page', 'Dashboard Overview')
        
        if current_page == "Dashboard Overview":
            self._render_dashboard_overview()
        elif current_page == "Student Management":
            student_page = StudentManagementPage()
            student_page.render()
        elif current_page == "Mark Attendance":
            attendance_page = AttendancePage()
            attendance_page.render()
        elif current_page == "Attendance Records":
            self._render_attendance_records()
        elif current_page == "Analytics":
            # Use the enhanced analytics page
            try:
                analytics_page = AnalyticsPage()
                analytics_page.render()
            except Exception as e:
                logger.error(f"Analytics error: {e}")
                st.error(f"❌ Analytics error: {str(e)}")
                st.info("💡 Try refreshing the page or check if students are registered")
        elif current_page == "User Management":
            self._render_user_management()
        elif current_page == "Danger Zone":
            self._render_danger_zone()
    
    def _render_user_dashboard(self, user: Dict):
        """Render user/student dashboard"""
        st.title("🎓 Student Dashboard")
        
        # Sidebar navigation
        self._render_user_sidebar(user)
        
        # Show current page
        current_page = st.session_state.get('current_page', 'User Dashboard')
        
        if current_page == "User Dashboard":
            self._render_user_dashboard_content()
        elif current_page == "Mark Attendance":
            attendance_page = AttendancePage()
            attendance_page.render()
    
    def _render_admin_sidebar(self, user: Dict):
        """Render admin sidebar navigation"""
        with st.sidebar:
            st.markdown("### 🎯 Admin Control Panel")
            
            # Navigation buttons with unique keys
            nav_buttons = [
                ("📈 Dashboard Overview", "Dashboard Overview", "admin_nav_dashboard"),
                ("👥 Student Management", "Student Management", "admin_nav_students"),
                ("📷 Mark Attendance", "Mark Attendance", "admin_nav_attendance"),
                ("📝 Attendance Records", "Attendance Records", "admin_nav_records"),
                ("📊 Analytics", "Analytics", "admin_nav_analytics"),
                ("👤 User Management", "User Management", "admin_nav_users"),
                ("⚠️ Danger Zone", "Danger Zone", "admin_nav_danger")
            ]
            
            for button_text, page_name, key in nav_buttons:
                if st.button(button_text, use_container_width=True, key=key):
                    st.session_state.current_page = page_name
                    st.rerun()
            
            st.markdown("---")
            self._render_user_info_sidebar(user)
    
    def _render_user_sidebar(self, user: Dict):
        """Render user sidebar navigation"""
        with st.sidebar:
            st.markdown("### 🎯 Student Panel")
            
            nav_buttons = [
                ("📈 My Dashboard", "User Dashboard", "user_nav_dashboard"),
                ("📷 Mark Attendance", "Mark Attendance", "user_nav_attendance")
            ]
            
            for button_text, page_name, key in nav_buttons:
                if st.button(button_text, use_container_width=True, key=key):
                    st.session_state.current_page = page_name
                    st.rerun()
            
            st.markdown("---")
            self._render_user_info_sidebar(user)
    
    def _render_user_info_sidebar(self, user: Dict):
        """Render user info and logout button"""
        st.markdown(f"**Logged in as:** {user['email']}")
        st.markdown(f"**Role:** {user['role'].title()}")
        
        if user.get('login_time'):
            st.markdown(f"**Login time:** {user['login_time'].strftime('%H:%M')}")
        
        # Add theme toggle
        st.markdown("---")
        st.markdown("### 🎨 Theme")
        try:
            from ui.components.theme_toggle import theme_toggle
            theme_toggle.render_toggle_button()
        except ImportError:
            pass  # Theme toggle not available
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, type="secondary", key="logout_btn"):
            self.session_manager.logout_user()
            st.rerun()
    
    def _render_dashboard_overview(self):
        """Render dashboard overview with safe error handling"""
        st.markdown("## 📈 Dashboard Overview")
        
        try:
            # Get today's stats with safe error handling
            stats = self._get_safe_attendance_stats()
            
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
            
            # Weekly trend if available
            weekly_rate = stats.get('avg_weekly_rate', 0)
            if weekly_rate > 0:
                trend_delta = attendance_rate - weekly_rate
                if trend_delta > 5:
                    st.success(f"📈 Attendance up {trend_delta:+.1f}% vs weekly average!")
                elif trend_delta < -5:
                    st.warning(f"📉 Attendance down {trend_delta:+.1f}% vs weekly average")
                else:
                    st.info(f"➡️ Attendance stable ({trend_delta:+.1f}% vs weekly average)")
            
            st.markdown("---")
            
            # Today's activity
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📅 Today's Attendance")
                self._render_safe_attendance_records()
            
            with col2:
                st.markdown("### 🎯 Quick Actions")
                self._render_quick_actions()
                
                # System status
                st.markdown("### 📊 System Status")
                self._render_system_status()
                
        except Exception as e:
            logger.error(f"Error rendering dashboard overview: {e}")
            st.error(f"❌ Dashboard error: {str(e)}")
            self._render_fallback_dashboard()
    
    def _get_safe_attendance_stats(self) -> Dict:
        """Get attendance stats with safe error handling"""
        try:
            if self.attendance_service:
                stats = self.attendance_service.get_today_attendance_summary()
                if stats:
                    return stats
            
            # Fallback to direct database query
            return self._get_basic_stats_from_db()
            
        except Exception as e:
            logger.error(f"Error getting attendance stats: {e}")
            return {
                'total_students': 0,
                'present_today': 0,
                'absent_today': 0,
                'attendance_rate': 0
            }
    
    def _get_basic_stats_from_db(self) -> Dict:
        """Get basic stats directly from database"""
        try:
            from database.connection import get_db_connection
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Total students
                cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = 1")
                total_students = cursor.fetchone()[0]
                
                # Present today
                cursor.execute("""
                    SELECT COUNT(DISTINCT student_id) 
                    FROM attendance 
                    WHERE date = ? AND time_in IS NOT NULL
                """, (str(date.today()),))
                present_today = cursor.fetchone()[0]
                
                absent_today = max(0, total_students - present_today)
                attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0
                
                return {
                    'total_students': total_students,
                    'present_today': present_today,
                    'absent_today': absent_today,
                    'attendance_rate': round(attendance_rate, 1)
                }
                
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}")
            return {}
    
    def _render_safe_attendance_records(self):
        """Render attendance records with safe error handling"""
        try:
            # Try to get today's records
            today_records = self._get_safe_attendance_records()
            
            if today_records and len(today_records) > 0:
                # Create DataFrame safely
                df = pd.DataFrame(today_records)
                
                # Ensure we have the required columns
                required_columns = ['name', 'roll_number', 'time_in', 'time_out']
                available_columns = [col for col in required_columns if col in df.columns]
                
                if available_columns:
                    display_df = df[available_columns].head(10)
                    
                    # Format time columns if they exist
                    for time_col in ['time_in', 'time_out']:
                        if time_col in display_df.columns:
                            display_df[time_col] = display_df[time_col].fillna('Not marked')
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "name": "Student Name",
                            "roll_number": "Roll Number",
                            "time_in": "Check In",
                            "time_out": "Check Out"
                        }
                    )
                else:
                    st.info("📝 No attendance column data available")
            else:
                st.info("No attendance records for today yet")
                
        except Exception as e:
            logger.error(f"Error rendering attendance records: {e}")
            st.warning("⚠️ Could not load today's attendance records")
    
    def _get_safe_attendance_records(self) -> List[Dict]:
        """Get attendance records with safe error handling"""
        try:
            if self.attendance_service:
                records = self.attendance_service.get_attendance_records(
                    start_date=date.today(),
                    end_date=date.today()
                )
                if records:
                    return records
            
            # Fallback to direct database query
            return self._get_basic_attendance_records()
            
        except Exception as e:
            logger.error(f"Error getting safe attendance records: {e}")
            return []
    
    def _get_basic_attendance_records(self) -> List[Dict]:
        """Get basic attendance records from database"""
        try:
            from database.connection import get_db_connection
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        s.name,
                        s.roll_number, 
                        a.time_in,
                        a.time_out,
                        a.status
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date = ?
                    ORDER BY a.created_at DESC
                    LIMIT 10
                """, (str(date.today()),))
                
                records = []
                for row in cursor.fetchall():
                    records.append({
                        'name': row['name'],
                        'roll_number': row['roll_number'],
                        'time_in': row['time_in'] or 'Not marked',
                        'time_out': row['time_out'] or 'Not marked',
                        'status': row['status']
                    })
                
                return records
                
        except Exception as e:
            logger.error(f"Error getting basic attendance records: {e}")
            return []
    
    def _render_quick_actions(self):
        """Render quick action buttons"""
        if st.button("➕ Add New Student", use_container_width=True, key="dashboard_add_student"):
            st.session_state.current_page = "Student Management"
            st.rerun()
        
        if st.button("📝 View All Records", use_container_width=True, key="dashboard_view_records"):
            st.session_state.current_page = "Attendance Records"
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True, key="dashboard_view_analytics"):
            st.session_state.current_page = "Analytics"
            st.rerun()
    
    def _render_system_status(self):
        """Render system status information"""
        try:
            if self.student_service:
                student_stats = self.student_service.get_student_statistics()
                
                st.metric("📚 Courses", len(student_stats.get('by_course', {})))
                st.metric("📸 With Photos", student_stats.get('with_photos', 0))
            else:
                # Fallback system status
                from database.connection import get_db_connection
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(DISTINCT course) FROM students WHERE is_active = 1")
                    course_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(DISTINCT student_id) FROM face_embeddings")
                    photo_count = cursor.fetchone()[0]
                    
                    st.metric("📚 Courses", course_count)
                    st.metric("📸 With Photos", photo_count)
                    
        except Exception as e:
            logger.error(f"Error rendering system status: {e}")
            st.warning("⚠️ System status unavailable")
    
    def _render_user_dashboard_content(self):
        """Render user dashboard content"""
        st.markdown("## 📊 Today's Overview")
        
        try:
            stats = self._get_safe_attendance_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 Total Students", stats.get('total_students', 0))
            
            with col2:
                present_today = stats.get('present_today', 0)
                absent_today = stats.get('absent_today', 0)
                st.metric("✅ Present Today", present_today, delta=f"{absent_today} absent")
            
            with col3:
                today_rate = stats.get('attendance_rate', 0)
                st.metric("📊 Attendance Rate", f"{today_rate:.1f}%")
            
            with col4:
                st.metric("📅 Today", date.today().strftime('%B %d, %Y'))
            
            # Recent attendance
            st.markdown("### 🕐 Recent Attendance")
            self._render_safe_attendance_records()
            
        except Exception as e:
            logger.error(f"Error rendering user dashboard: {e}")
            st.error(f"❌ Error loading dashboard: {str(e)}")
    
    def _render_fallback_dashboard(self):
        """Render basic fallback dashboard when main dashboard fails"""
        st.warning("⚠️ Dashboard experiencing issues. Showing basic information.")
        
        try:
            from database.connection import get_db_connection
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = 1")
                student_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (str(date.today()),))
                attendance_count = cursor.fetchone()[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📚 Total Students", student_count)
                with col2:
                    st.metric("📋 Today's Records", attendance_count)
                
                # Quick actions
                st.markdown("### 🎯 Quick Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👥 Students", key="fallback_students"):
                        st.session_state.current_page = "Student Management"
                        st.rerun()
                
                with col2:
                    if st.button("📷 Attendance", key="fallback_attendance"):
                        st.session_state.current_page = "Mark Attendance"
                        st.rerun()
                
                with col3:
                    if st.button("📊 Records", key="fallback_records"):
                        st.session_state.current_page = "Attendance Records"
                        st.rerun()
                
        except Exception as e:
            st.error(f"❌ Critical error: {str(e)}")
            st.info("💡 Try restarting the application or check your database connection")
    
    def _render_attendance_records(self):
        """Render attendance records page"""
        st.markdown("## 📝 Attendance Records")
        
        try:
            # Date range selector
            col1, col2, col3 = st.columns(3)
            
            with col1:
                start_date = st.date_input("📅 Start Date", value=date.today() - timedelta(days=7))
            
            with col2:
                end_date = st.date_input("📅 End Date", value=date.today())
            
            with col3:
                if st.button("🔍 Filter Records", use_container_width=True):
                    st.rerun()
            
            # Get records
            if self.attendance_service:
                records = self.attendance_service.get_attendance_records(start_date, end_date)
            else:
                records = self._get_attendance_records_fallback(start_date, end_date)
            
            if records:
                # Display as DataFrame
                df = pd.DataFrame(records)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Export option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"attendance_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("📝 No records found for the selected date range")
                
        except Exception as e:
            logger.error(f"Error rendering attendance records: {e}")
            st.error(f"❌ Error loading records: {str(e)}")
    
    def _get_attendance_records_fallback(self, start_date: date, end_date: date) -> List[Dict]:
        """Fallback method to get attendance records"""
        try:
            from database.connection import get_db_connection
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        s.name as student_name,
                        s.roll_number,
                        s.course,
                        a.date,
                        a.time_in,
                        a.time_out,
                        a.status,
                        a.marked_by
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date BETWEEN ? AND ?
                    ORDER BY a.date DESC, a.time_in DESC
                """, (str(start_date), str(end_date)))
                
                records = []
                for row in cursor.fetchall():
                    records.append(dict(row))
                
                return records
                
        except Exception as e:
            logger.error(f"Error getting attendance records fallback: {e}")
            return []
    
    def _render_user_management(self):
        """Render user management page"""
        st.markdown("## 👤 User Management")
        
        try:
            # Add new user section
            with st.expander("➕ Add New User"):
                with st.form("add_user_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_email = st.text_input("📧 Email")
                        new_password = st.text_input("🔒 Password", type="password")
                    
                    with col2:
                        new_role = st.selectbox("👤 Role", ["user", "admin"])
                        confirm_password = st.text_input("🔒 Confirm Password", type="password")
                    
                    if st.form_submit_button("➕ Add User"):
                        if new_password == confirm_password:
                            try:
                                from auth.user_service import UserService
                                user_service = UserService()
                                success, message = user_service.create_user(new_email, new_password, new_role)
                                
                                if success:
                                    st.success(f"✅ User {new_email} added successfully!")
                                else:
                                    st.error(f"❌ Error: {message}")
                            except Exception as e:
                                st.error(f"❌ Error adding user: {str(e)}")
                        else:
                            st.error("❌ Passwords do not match")
            
            # Existing users
            st.markdown("### 👥 Current Users")
            
            try:
                from database.connection import get_db_connection
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, email, role, created_at FROM users ORDER BY created_at DESC")
                    users = cursor.fetchall()
                
                if users:
                    users_df = pd.DataFrame(users)
                    st.dataframe(users_df, use_container_width=True, hide_index=True)
                else:
                    st.info("👤 No users found")
                    
            except Exception as e:
                st.error(f"❌ Error loading users: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in user management: {e}")
            st.error(f"❌ User management error: {str(e)}")
    
    def _render_danger_zone(self):
        """Render danger zone page"""
        st.markdown("## ⚠️ Danger Zone")
        st.error("🚨 **Warning:** These actions are irreversible!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🗑️ Delete All Data")
            st.warning("This will delete ALL students, attendance records, and face data")
            
            if st.button("🗑️ Delete All Students", type="secondary"):
                if st.session_state.get('confirm_delete_all') == 'confirmed':
                    try:
                        from database.connection import get_db_connection
                        
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM face_embeddings")
                            cursor.execute("DELETE FROM attendance")
                            cursor.execute("DELETE FROM students")
                            conn.commit()
                        
                        st.success("✅ All data deleted successfully")
                        st.session_state.confirm_delete_all = None
                    except Exception as e:
                        st.error(f"❌ Error deleting data: {str(e)}")
                else:
                    st.session_state.confirm_delete_all = 'confirmed'
                    st.warning("⚠️ Click again to confirm deletion")
        
        with col2:
            st.markdown("### 📊 System Reset")
            st.info("Reset system to initial state")
            
            if st.button("🔄 Reset System", type="secondary"):
                if st.session_state.get('confirm_reset') == 'confirmed':
                    try:
                        from database.initialization import init_database
                        init_database()
                        st.success("✅ System reset successfully")
                        st.session_state.confirm_reset = None
                    except Exception as e:
                        st.error(f"❌ Error resetting system: {str(e)}")
                else:
                    st.session_state.confirm_reset = 'confirmed'
                    st.warning("⚠️ Click again to confirm reset")
