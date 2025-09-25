"""
Application configuration settings
Extracted from constants across all modules
"""
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

def get_config_value(key, default=None):
    """Get configuration value from Streamlit secrets or environment variables"""
    # First try environment variables (.env file for localhost)
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    # Then try Streamlit secrets (for cloud deployment)
    try:
        return st.secrets[key]
    except Exception:
        # Return default if neither source has the value
        return default

# Base paths
BASE_DIR = Path(__file__).parent.parent
DB_FILE = BASE_DIR / "data" / "attendance.db"
STATIC_DIR = BASE_DIR / "static"

# Security constants (updated to use secrets)
SALT = get_config_value("SALT", "attendance_system_salt_2024")
SECRET_KEY = get_config_value("SECRET_KEY", "smart_attendance_secret_key_2024")
TOKEN_EXPIRY_HOURS = int(get_config_value("TOKEN_EXPIRY_HOURS", "1"))
MIN_PASSWORD_LENGTH = int(get_config_value("MIN_PASSWORD_LENGTH", "6"))

# Admin credentials (NEW - from secrets)
ADMIN_EMAIL = get_config_value("ADMIN_EMAIL", "admin@gmail.com")
ADMIN_PASSWORD = get_config_value("ADMIN_PASSWORD", "admin123")
ADMIN_ROLE = get_config_value("ADMIN_ROLE", "admin")

# Face recognition constants
MODEL_NAME = get_config_value("MODEL_NAME", "ArcFace")
DETECTOR_BACKEND = get_config_value("DETECTOR_BACKEND", "retinaface")
EMBEDDING_SIZE = int(get_config_value("EMBEDDING_SIZE", "512"))
RECOGNITION_THRESHOLD = float(get_config_value("RECOGNITION_THRESHOLD", "0.5"))
FACE_CONFIDENCE_THRESHOLD = float(get_config_value("SIMILARITY_THRESHOLD", "0.4"))

# UI settings
PAGE_TITLE = "🎓 Smart Face Attendance System"
PAGE_ICON = "🎓"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Database settings
DB_TIMEOUT = int(get_config_value("DB_TIMEOUT", "30"))
ENABLE_FOREIGN_KEYS = True

# Streamlit session keys
SESSION_KEYS = {
    'LOGIN_STATUS': 'login_status',
    'USERNAME': 'username', 
    'USER_ROLE': 'user_role',
    'USER_EMAIL': 'user_email'
}

# Email validation pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
