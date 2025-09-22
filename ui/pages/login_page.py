"""
Login page component
Extracted from app.py login functionality
"""
import streamlit as st
import time
import logging
from typing import Optional, Dict, Tuple
from auth.authentication import AuthenticationService
from auth.session_manager import SessionManager
from ui.components.forms import LoginForm, SignupForm
from config.settings import SESSION_KEYS
from ui.components.theme_toggle import theme_toggle
logger = logging.getLogger(__name__)

class LoginPage:
    """Login page component"""
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        self.session_manager = SessionManager()
    
    def render(self):
        """Render complete login page"""
        col1, col2, col3 = st.columns([6, 1, 1])
        with col3:
            theme_toggle.render_toggle_button()
        st.title("🎓 Smart Face Attendance System")
        st.markdown("### 🔐 Secure Authentication Portal")
        
        # Create tabs for different auth options
        tab1, tab2, tab3 = st.tabs(["🔑 Login", "👤 Sign Up", "🔒 Forgot Password"])
        
        with tab1:
            self._render_login_tab()
        
        with tab2:
            self._render_signup_tab()
        
        with tab3:
            self._render_forgot_password_tab()
        
        # Handle password reset if token is available
        if st.session_state.get('show_password_reset', False):
            self._render_password_reset_form()
    
    def _render_login_tab(self):
        """Render login tab"""
        st.markdown("#### Welcome Back!")
        
        # Use form component
        email, password, submitted = LoginForm.render()
        
        if submitted:
            self._handle_login(email, password)
        
        # Demo credentials info
        st.info("🔑 **Demo Credentials:**\n- Email: admin@attendance.com\n- Password: admin123")
    
    def _render_signup_tab(self):
        """Render signup tab"""
        st.markdown("#### Create New Account")
        
        # Use form component
        user_data, submitted = SignupForm.render()
        
        if submitted and user_data:
            self._handle_signup(user_data)
    
    def _render_forgot_password_tab(self):
        """Render forgot password tab"""
        st.markdown("#### Reset Your Password")
        self._render_forgot_password_form()
    
    def _render_forgot_password_form(self):
        """Forgot password form"""
        st.info("💡 Enter your email to receive password reset instructions")
        
        with st.form("forgot_password_form"):
            email = st.text_input("📧 Email Address", placeholder="Enter your registered email")
            reset_btn = st.form_submit_button("📤 Send Reset Link", use_container_width=True)
            
            if reset_btn and email:
                self._handle_password_reset_request(email)
    
    def _render_password_reset_form(self):
        """Password reset form using token"""
        st.markdown("---")
        st.markdown("#### 🔄 Set New Password")
        
        with st.form("password_reset_form"):
            st.info(f"🔐 Resetting password for: **{st.session_state.get('reset_email', '')}**")
            
            reset_token = st.text_input(
                "🎫 Reset Token",
                value=st.session_state.get('reset_token', ''),
                help="Paste the reset token from above"
            )
            
            new_password = st.text_input(
                "🔒 New Password", 
                type="password",
                placeholder="Enter new password (min 6 characters)"
            )
            
            confirm_new_password = st.text_input(
                "🔒 Confirm New Password", 
                type="password",
                placeholder="Confirm new password"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                reset_password_btn = st.form_submit_button("🔄 Reset Password", use_container_width=True)
            with col2:
                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True, type="secondary")
            
            if reset_password_btn:
                self._handle_password_reset(reset_token, new_password, confirm_new_password)
            
            if cancel_btn:
                self._clear_password_reset_session()
                st.rerun()
    
    def _handle_login(self, email: str, password: str):
        """Handle login submission"""
        if not email or not password:
            st.error("⚠️ Please fill in all fields")
            return
        
        with st.spinner("🔐 Authenticating..."):
            success, message, user_data = self.auth_service.login_user(email, password)
            
            if success and user_data:
                # Set session
                self.session_manager.login_user(user_data)
                st.success("🎉 Login successful!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    def _handle_signup(self, user_data: Dict):
        """Handle signup submission"""
        with st.spinner("📝 Creating account..."):
            success, message = self.auth_service.signup_user(
                user_data['username'],
                user_data['email'],
                user_data['password']
            )
            
            if success:
                st.success(f"✅ {message}. You can now login!")
                st.balloons()
            else:
                st.error(f"❌ {message}")
    
    def _handle_password_reset_request(self, email: str):
        """Handle password reset request"""
        with st.spinner("📤 Processing reset request..."):
            success, message, token = self.auth_service.initiate_password_reset(email)
            
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
    
    def _handle_password_reset(self, token: str, new_password: str, confirm_password: str):
        """Handle password reset with token"""
        if not all([token, new_password, confirm_password]):
            st.error("⚠️ Please fill in all fields")
            return
        
        if new_password != confirm_password:
            st.error("❌ Passwords do not match")
            return
        
        email = st.session_state.get('reset_email', '')
        
        with st.spinner("🔄 Resetting password..."):
            success, message = self.auth_service.reset_password(email, token, new_password)
            
            if success:
                st.success("✅ Password reset successful! You can now login.")
                st.balloons()
                self._clear_password_reset_session()
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    def _clear_password_reset_session(self):
        """Clear password reset session data"""
        keys_to_clear = ['reset_token', 'reset_email', 'show_password_reset']
        for key in keys_to_clear:
            st.session_state.pop(key, None)
