"""
User data repository
Extracted from auth.py user-related functions
"""
import logging
from typing import List, Dict, Optional, Tuple  # Added missing imports
from datetime import datetime, timedelta
from database.connection import get_db_connection

logger = logging.getLogger(__name__)

class UserRepository:
    """Handle all user-related database operations"""
    
    def create_user(self, username: str, email: str, password_hash: str, 
                   role: str = 'user') -> Tuple[bool, str]:
        """Create new user in database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", 
                             (email, username))
                if cursor.fetchone():
                    return False, "User with this email or username already exists"
                
                # Insert user
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, password_hash, role))
                
                conn.commit()
                logger.info(f"User {username} created successfully")
                return True, "User created successfully"
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, f"Error creating user: {str(e)}"
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, password_hash, role, created_at, last_login
                    FROM users WHERE email = ?
                ''', (email,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row['id'],
                        'username': row['username'],
                        'email': row['email'],
                        'password_hash': row['password_hash'],
                        'role': row['role'],
                        'created_at': row['created_at'],
                        'last_login': row['last_login']
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def update_last_login(self, email: str) -> bool:
        """Update user's last login timestamp"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE email = ?
                ''', (email,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, username, email, role, created_at, last_login
                    FROM users ORDER BY created_at DESC
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row['id'],
                        'username': row['username'],
                        'email': row['email'],
                        'role': row['role'],
                        'created_at': row['created_at'],
                        'last_login': row['last_login']
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete user by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists and get info
                cursor.execute("SELECT username, email, role FROM users WHERE id = ?", (user_id,))
                user = cursor.fetchone()
                if not user:
                    return False, "User not found"
                
                # Prevent deletion of admin users
                if user['role'] == 'admin':
                    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                    admin_count = cursor.fetchone()[0]
                    if admin_count <= 1:
                        return False, "Cannot delete the last admin user"
                
                # Delete user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                
                logger.info(f"User {user['username']} deleted")
                return True, f"User {user['username']} deleted successfully"
                
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False, f"Error deleting user: {str(e)}"
    
    def store_reset_token(self, email: str, token: str, expires: datetime) -> bool:
        """Store password reset token"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET reset_token = ?, reset_token_expires = ?
                    WHERE email = ?
                ''', (token, expires, email))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error storing reset token: {e}")
            return False
    
    def verify_reset_token(self, email: str, token: str) -> bool:
        """Verify password reset token"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT reset_token, reset_token_expires 
                    FROM users WHERE email = ?
                ''', (email,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                stored_token = result['reset_token']
                expires = datetime.fromisoformat(result['reset_token_expires']) if result['reset_token_expires'] else None
                
                if stored_token == token and expires and expires > datetime.now():
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error verifying reset token: {e}")
            return False
    
    def update_password(self, email: str, new_password_hash: str) -> bool:
        """Update user password and clear reset token"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
                    WHERE email = ?
                ''', (new_password_hash, email))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False
    
    def delete_all_users_except_admin(self) -> Tuple[bool, str]:
        """Delete all non-admin users"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get count of non-admin users
                cursor.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    return False, "No non-admin users to delete"
                
                # Delete non-admin users
                cursor.execute("DELETE FROM users WHERE role != 'admin'")
                conn.commit()
                
                logger.info(f"Deleted {count} non-admin users")
                return True, f"Successfully deleted {count} users (admins preserved)"
                
        except Exception as e:
            logger.error(f"Error deleting users: {e}")
            return False, f"Error deleting users: {str(e)}"
