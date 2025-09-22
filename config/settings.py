"""
Application configuration settings
Extracted from constants across all modules
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DB_FILE = BASE_DIR / "data" / "attendance.db"
STATIC_DIR = BASE_DIR / "static"

# Security constants (from auth.py)
SALT = os.getenv("SALT", "attendance_system_salt_2024")
TOKEN_EXPIRY_HOURS = 1
MIN_PASSWORD_LENGTH = 6

# Face recognition constants (from face_utils.py)
# Face recognition constants (from face_utils.py)
MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "retinaface"
EMBEDDING_SIZE = 512
RECOGNITION_THRESHOLD = 0.5  # Lowered from 0.6 to 0.5
FACE_CONFIDENCE_THRESHOLD = 0.4  # Alternative threshold

# UI settings (from app.py)
PAGE_TITLE = "🎓 Smart Face Attendance System"
PAGE_ICON = "🎓"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Database settings (from db.py)
DB_TIMEOUT = 30
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
