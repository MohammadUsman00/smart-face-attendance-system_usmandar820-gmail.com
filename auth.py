import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from db import get_db_connection
from dotenv import load_dotenv
import re
import os

load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security constants
SALT = "attendance_system_salt_2024"
TOKEN_EXPIRY_HOURS = 1
MIN_PASSWORD_LENGTH = 6

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Enhanced password validation"""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    # Check for at least one letter and one number (optional for demo)
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    # Relaxed validation - don't require number for demo
    # if not re.search(r'\d', password):
    #     return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def hash_password(password):
    """Hash password using SHA-256 with salt"""
    return hashlib.sha256((password + SALT).encode()).hexdigest()

def verify_password(password, stored_hash):
    """Verify password against stored hash"""
    return hash_password(password) == stored_hash

def generate_reset_token():
    """Generate secure reset token"""
    return secrets.token_urlsafe(32)

def signup_user(email, password, role='user'):
    """Register new user with enhanced validation"""
    try:
        # Input validation
        if not email or not password:
            return False, "Email and password are required", None
        
        email = email.strip().lower()
        
        # Email validation
        if not validate_email(email):
            return False, "Invalid email format", None
        
        # Password validation (relaxed for demo)
        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long", None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "User with this email already exists", None
            
            # Create user
            hashed_password = hash_password(password)
            cursor.execute("""
                INSERT INTO users (email, password, role)
                VALUES (?, ?, ?)
            """, (email, hashed_password, role))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"New user registered: {email} (role: {role})")
            return True, "User registered successfully", {
                "id": user_id, 
                "email": email, 
                "role": role
            }
            
    except Exception as e:
        logger.error(f"Signup error for {email}: {e}")
        return False, f"Registration failed: {str(e)}", None

def login_user(email, password):
    """Authenticate user login with enhanced security"""
    try:
        # Input validation
        if not email or not password:
            return False, "Email and password are required", None
        
        email = email.strip().lower()
        
        # Email format validation
        if not validate_email(email):
            logger.warning(f"Login attempt with invalid email format: {email}")
            return False, "Invalid email format", None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, password, role, created_at
                FROM users WHERE email = ?
            """, (email,))
            
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                if verify_password(password, user_dict['password']):
                    # Remove password from returned data for security
                    del user_dict['password']
                    logger.info(f"Successful login: {email} (role: {user_dict['role']})")
                    return True, "Login successful", user_dict
                else:
                    logger.warning(f"Failed login attempt: {email} (wrong password)")
                    return False, "Invalid email or password", None
            else:
                logger.warning(f"Failed login attempt: {email} (user not found)")
                return False, "Invalid email or password", None
                
    except Exception as e:
        logger.error(f"Login error for {email}: {e}")
        return False, f"Login error: {str(e)}", None

def initiate_password_reset(email):
    """Initiate password reset process"""
    try:
        email = email.strip().lower()
        if not validate_email(email):
            return False, "Invalid email format", None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                # Don't reveal if email exists for security
                return True, "If the email exists, a reset link has been sent", None
            
            # Generate reset token
            reset_token = generate_reset_token()
            expires_at = datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
            
            # Store reset token
            cursor.execute("""
                UPDATE users 
                SET reset_token = ?, reset_token_expires = ? 
                WHERE email = ?
            """, (reset_token, expires_at, email))
            
            conn.commit()
            
            logger.info(f"Password reset initiated for: {email}")
            
            # In production, send email here
            # For demo, return token directly
            return True, "Reset token generated", reset_token
            
    except Exception as e:
        logger.error(f"Password reset error for {email}: {e}")
        return False, "Password reset failed. Please try again.", None

def reset_password(email, token, new_password):
    """Reset password using token"""
    try:
        email = email.strip().lower()
        
        # Validate inputs
        if not all([email, token, new_password]):
            return False, "All fields are required"
        
        if not validate_email(email):
            return False, "Invalid email format"
        
        # Password validation (relaxed for demo)
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verify reset token (SQLite datetime comparison)
            cursor.execute("""
                SELECT id FROM users 
                WHERE email = ? AND reset_token = ? 
                AND reset_token_expires > datetime('now')
            """, (email, token))
            
            user = cursor.fetchone()
            if not user:
                return False, "Invalid or expired reset token"
            
            # Update password and clear reset token
            hashed_password = hash_password(new_password)
            cursor.execute("""
                UPDATE users 
                SET password = ?, reset_token = NULL, reset_token_expires = NULL 
                WHERE email = ?
            """, (hashed_password, email))
            
            conn.commit()
            
            logger.info(f"Password reset completed for: {email}")
            return True, "Password reset successfully"
            
    except Exception as e:
        logger.error(f"Password reset completion error for {email}: {e}")
        return False, "Password reset failed. Please try again."

def change_password(user_id, current_password, new_password):
    """Change user password"""
    try:
        # Validate inputs
        if not current_password or not new_password:
            return False, "Both current and new passwords are required"
        
        # Password validation (relaxed for demo)
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verify current password
            cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user or not verify_password(current_password, user['password']):
                return False, "Current password is incorrect"
            
            # Update password
            hashed_password = hash_password(new_password)
            cursor.execute("""
                UPDATE users SET password = ? WHERE id = ?
            """, (hashed_password, user_id))
            
            conn.commit()
            
            logger.info(f"Password changed for user ID: {user_id}")
            return True, "Password changed successfully"
            
    except Exception as e:
        logger.error(f"Password change error for user {user_id}: {e}")
        return False, "Password change failed. Please try again."

def get_all_users():
    """Get all users (admin only)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, role, created_at
                FROM users 
                ORDER BY role DESC, created_at DESC
            """)
            
            rows = cursor.fetchall()
            users = [dict(row) for row in rows]
            
            logger.info(f"Retrieved {len(users)} users")
            return users
            
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return []

def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists and is not admin
            cursor.execute("SELECT email, role FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False, "User not found"
            
            user_dict = dict(user)
            if user_dict['role'] == 'admin':
                return False, "Cannot delete admin user"
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
            logger.info(f"User deleted: {user_dict['email']} (ID: {user_id})")
            return True, "User deleted successfully"
            
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return False, "Failed to delete user"

def get_user_stats():
    """Get user statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Users by role
            cursor.execute("""
                SELECT role, COUNT(*) FROM users GROUP BY role
            """)
            roles = dict(cursor.fetchall())
            
            # Recent registrations (last 30 days) 
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= datetime('now', '-30 days')
            """)
            recent_registrations = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'roles': roles,
                'recent_registrations': recent_registrations
            }
            
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {
            'total_users': 0,
            'roles': {},
            'recent_registrations': 0
        }

def cleanup_expired_tokens():
    """Cleanup expired reset tokens"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET reset_token = NULL, reset_token_expires = NULL 
                WHERE reset_token_expires < datetime('now')
            """)
            
            cleaned_count = cursor.rowcount
            conn.commit()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired reset tokens")
                
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, role, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
            
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def update_user_role(user_id, new_role):
    """Update user role (admin only)"""
    try:
        valid_roles = ['user', 'admin']
        if new_role not in valid_roles:
            return False, "Invalid role"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET role = ? WHERE id = ?
            """, (new_role, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Updated role for user {user_id} to {new_role}")
                return True, "Role updated successfully"
            else:
                return False, "User not found"
                
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        return False, "Failed to update role"

def is_admin(user_id):
    """Check if user is admin"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return user and user['role'] == 'admin'
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def get_user_by_email(email):
    """Get user by email"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, role, created_at
                FROM users WHERE email = ?
            """, (email,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
            
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

# Initialize cleanup on import
cleanup_expired_tokens()

logger.info("Enhanced authentication module loaded with password reset and SQLite support")
