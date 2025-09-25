"""
Authentication service
Extracted from auth.py authentication functions
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, List  # Added missing imports


from config.settings import SALT, TOKEN_EXPIRY_HOURS
from database.user_repository import UserRepository
from auth.validators import validate_email, validate_password, validate_username, sanitize_input


logger = logging.getLogger(__name__)


class AuthenticationService:
    """Handle user authentication operations"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        return hashlib.sha256((password + SALT).encode()).hexdigest()
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        return self.hash_password(password) == stored_hash
    
    def generate_secure_token(self) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    def signup_user(self, username: str, email: str, password: str, 
                   role: str = 'user') -> Tuple[bool, str]:
        """Register new user"""
        try:
            # Sanitize inputs
            username = sanitize_input(username)
            email = sanitize_input(email).lower()
            role = sanitize_input(role).lower()
            
            # Validate inputs
            if not validate_email(email):
                return False, "Invalid email format"
            
            username_valid, username_msg = validate_username(username)
            if not username_valid:
                return False, username_msg
            
            password_valid, password_msg = validate_password(password)
            if not password_valid:
                return False, password_msg
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user in database
            success, message = self.user_repo.create_user(username, email, password_hash, role)
            
            if success:
                logger.info(f"New user registered: {email}")
            else:
                logger.warning(f"User registration failed: {email} - {message}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error in user signup: {e}")
            return False, f"Registration failed: {str(e)}"
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user login"""
        try:
            # Sanitize inputs
            email = sanitize_input(email).lower()
            
            # Validate email format
            if not validate_email(email):
                return False, "Invalid email format", None
            
            # Get user from database
            user = self.user_repo.get_user_by_email(email)
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return False, "Invalid email or password", None
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                logger.warning(f"Failed login attempt for: {email}")
                return False, "Invalid email or password", None
            
            # Update last login
            self.user_repo.update_last_login(email)
            
            # Return user info (excluding password hash)
            user_info = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            }
            
            logger.info(f"Successful login: {email}")
            return True, "Login successful", user_info
            
        except Exception as e:
            logger.error(f"Error in user login: {e}")
            return False, f"Login failed: {str(e)}", None
    
    def initiate_password_reset(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """Initiate password reset process"""
        try:
            email = sanitize_input(email).lower()
            
            if not validate_email(email):
                return False, "Invalid email format", None
            
            # Check if user exists
            user = self.user_repo.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists or not for security
                return True, "If the email exists, a reset link will be sent", None
            
            # Generate reset token
            reset_token = self.generate_secure_token()
            expires = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
            
            # Store token in database
            success = self.user_repo.store_reset_token(email, reset_token, expires)
            
            if success:
                # Send email with reset token
                try:
                    from utils.email_service import EmailService
                    email_service = EmailService()
                    email_sent, email_message = email_service.send_password_reset_email(email, reset_token)
                    
                    logger.info(f"Password reset initiated for: {email}")
                    return True, email_message, reset_token
                    
                except Exception as email_error:
                    logger.error(f"Email service error: {email_error}")
                    # Fallback: return token directly
                    return True, f"🔑 Reset token generated: {reset_token}", reset_token
            else:
                return False, "Failed to generate reset token", None
                
        except Exception as e:
            logger.error(f"Error initiating password reset: {e}")
            return False, f"Password reset failed: {str(e)}", None
    
    def reset_password(self, email: str, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password with token"""
        try:
            email = sanitize_input(email).lower()
            
            # Validate inputs
            if not validate_email(email):
                return False, "Invalid email format"
            
            password_valid, password_msg = validate_password(new_password)
            if not password_valid:
                return False, password_msg
            
            # Verify reset token
            if not self.user_repo.verify_reset_token(email, token):
                logger.warning(f"Invalid or expired reset token for: {email}")
                return False, "Invalid or expired reset token"
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            success = self.user_repo.update_password(email, new_password_hash)
            
            if success:
                logger.info(f"Password reset successful for: {email}")
                return True, "Password reset successful"
            else:
                return False, "Failed to update password"
                
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False, f"Password reset failed: {str(e)}"
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        return self.user_repo.get_all_users()
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete user (admin only)"""
        return self.user_repo.delete_user(user_id)


# Standalone functions for backward compatibility
def hash_password(password: str) -> str:
    """Standalone hash password function"""
    auth_service = AuthenticationService()
    return auth_service.hash_password(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Standalone verify password function"""
    auth_service = AuthenticationService()
    return auth_service.verify_password(password, stored_hash)


def generate_secure_token() -> str:
    """Standalone token generation function"""
    auth_service = AuthenticationService()
    return auth_service.generate_secure_token()
