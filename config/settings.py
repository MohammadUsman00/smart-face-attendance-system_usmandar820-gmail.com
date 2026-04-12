"""
Application configuration settings
Extracted from constants across all modules
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

def get_config_value(key, default=None):
    """
    Config from environment only (python-dotenv loads .env into os.environ at import time).
    Do not use st.secrets here — it can re-enter Streamlit and cause RecursionError.
    For Streamlit Cloud, set variables in the dashboard or use secrets.toml → env injection.
    """
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
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
# Admin TOTP (Google Authenticator–compatible); off by default
ENABLE_ADMIN_2FA = get_config_value("ENABLE_ADMIN_2FA", "false").lower() in ("1", "true", "yes")
# Password reset abuse control
PASSWORD_RESET_MAX_PER_HOUR = int(get_config_value("PASSWORD_RESET_MAX_PER_HOUR", "5"))

# Admin credentials (NEW - from secrets)
ADMIN_EMAIL = get_config_value("ADMIN_EMAIL", "admin@gmail.com")
ADMIN_PASSWORD = get_config_value("ADMIN_PASSWORD", "admin123")
ADMIN_ROLE = get_config_value("ADMIN_ROLE", "admin")

# Face recognition constants
MODEL_NAME = get_config_value("MODEL_NAME", "ArcFace")
DETECTOR_BACKEND = get_config_value("DETECTOR_BACKEND", "retinaface")
EMBEDDING_SIZE = int(get_config_value("EMBEDDING_SIZE", "512"))
RECOGNITION_THRESHOLD = float(get_config_value("RECOGNITION_THRESHOLD", "0.5"))
# Minimum gap between best and second-best *student* similarity (reduces lookalike swaps).
RECOGNITION_MARGIN = float(get_config_value("RECOGNITION_MARGIN", "0.08"))
FACE_CONFIDENCE_THRESHOLD = float(get_config_value("SIMILARITY_THRESHOLD", "0.4"))
# When false, do not embed the whole frame without a face box (safer; may require clearer photos).
ALLOW_SKIP_DETECTION_FALLBACK = get_config_value(
    "ALLOW_SKIP_DETECTION_FALLBACK", "false"
).lower() in ("1", "true", "yes")

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

# Live mask WebRTC (process every Nth frame for CPU; higher = lighter)
MASK_FRAME_SKIP = int(get_config_value("MASK_FRAME_SKIP", "2"))

# Block attendance if mask detector is not confident the face is uncovered
MASK_BLOCK_UNCERTAIN = get_config_value("MASK_BLOCK_UNCERTAIN", "true").lower() in (
    "1",
    "true",
    "yes",
)

# Run mask / covering check before face recognition at attendance
ATTENDANCE_MASK_CHECK_ENABLED = get_config_value("ATTENDANCE_MASK_CHECK_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)

# YOLO-World (pretrained, no training) — mask vs no-mask via open vocabulary
MASK_USE_YOLO = get_config_value("MASK_USE_YOLO", "true").lower() in ("1", "true", "yes")
MASK_YOLO_MODEL = get_config_value("MASK_YOLO_MODEL", "yolov8s-worldv2.pt")
MASK_YOLO_DEVICE = get_config_value("MASK_YOLO_DEVICE", "cpu")
MASK_YOLO_CONF_MASK = float(get_config_value("MASK_YOLO_CONF_MASK", "0.22"))
MASK_YOLO_CONF_NOMASK = float(get_config_value("MASK_YOLO_CONF_NOMASK", "0.32"))
YOLO_CLASS_MASK_TEXT = get_config_value(
    "YOLO_CLASS_MASK_TEXT",
    "person wearing a medical face mask covering nose and mouth",
)
YOLO_CLASS_NOMASK_TEXT = get_config_value(
    "YOLO_CLASS_NOMASK_TEXT",
    "human face without mask nose and mouth visible",
)
