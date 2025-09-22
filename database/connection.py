"""
Database connection management
Extracted from db.py get_db_connection and init functions
"""
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from config.settings import DB_FILE, DB_TIMEOUT, ENABLE_FOREIGN_KEYS

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """SQLite connection context manager with proper error handling"""
    connection = None
    try:
        # Ensure database directory exists
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        connection = sqlite3.connect(str(DB_FILE), timeout=DB_TIMEOUT)
        connection.row_factory = sqlite3.Row  # Enable dict-like access
        
        if ENABLE_FOREIGN_KEYS:
            connection.execute("PRAGMA foreign_keys = ON")
        
        yield connection
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def init_database():
    """Initialize database with all required tables and admin user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reset_token TEXT,
                    reset_token_expires TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # Create students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    course TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create face_embeddings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    embedding_data TEXT NOT NULL,
                    photo_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
                )
            ''')
            
            # Create attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    time_in TIMESTAMP,
                    time_out TIMESTAMP,
                    status TEXT DEFAULT 'present',
                    marked_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                    UNIQUE(student_id, date)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            
            conn.commit()
            
            # Create default admin user
            _create_default_admin(cursor, conn)
            
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def _create_default_admin(cursor, conn):
    """Create default admin user if not exists"""
    import hashlib
    from config.settings import SALT
    
    try:
        # Check if admin exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Create default admin
            admin_password = "admin123"
            password_hash = hashlib.sha256((admin_password + SALT).encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin", "admin@attendance.com", password_hash, "admin"))
            
            conn.commit()
            logger.info("Default admin user created: admin@attendance.com / admin123")
            
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
