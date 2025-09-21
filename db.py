import sqlite3
import os
from datetime import date, datetime, timedelta
import hashlib
import numpy as np
import logging
from contextlib import contextmanager
import base64
import pandas as pd

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_FILE = "attendance.db"
EMBEDDING_SIZE = 512

@contextmanager
def get_db_connection():
    """SQLite connection context manager with proper error handling"""
    connection = None
    try:
        connection = sqlite3.connect(DB_FILE, timeout=30)
        connection.row_factory = sqlite3.Row  # Enable dict-like access
        connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
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
    """Initialize database with all required tables and admin user - FIXED FUNCTION NAME"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table with password reset fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    reset_token TEXT,
                    reset_token_expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create students table with enhanced course options
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    course TEXT NOT NULL DEFAULT 'CSE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create face_embeddings table for multi-photo support
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    embedding TEXT NOT NULL,
                    photo_number INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)
            
            # Create attendance table with dual tracking (IN/OUT)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    time_in TEXT,
                    time_out TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    UNIQUE(student_id, date)
                )
            """)
            
            conn.commit()
            
            # Create default admin user
            cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@gmail.com",))
            if not cursor.fetchone():
                hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
                    ("admin@gmail.com", hashed_password, 'admin')
                )
                conn.commit()
                logger.info("Default admin user created: admin@gmail.com / admin123")
            
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def add_student_with_photos(name, roll_number, email, phone=None, course="CSE", images=None):
    """Add student with multiple photos and enhanced validation"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Validate required fields
            if not all([name, roll_number, email]):
                return False, "Name, roll number, and email are required"
            
            # Validate course
            valid_courses = ["CSE", "CE", "EE", "BE", "ME"]
            if course not in valid_courses:
                course = "CSE"  # Default fallback
            
            # Insert student record
            cursor.execute("""
                INSERT INTO students (name, roll_number, email, phone, course)
                VALUES (?, ?, ?, ?, ?)
            """, (name, roll_number, email, phone, course))
            
            student_id = cursor.lastrowid
            
            # Process and store face embeddings
            if images:
                import face_utils as fu
                embeddings_added = 0
                
                for i, img in enumerate(images, 1):
                    try:
                        embedding = fu.image_to_embedding_bgr(img)
                        if embedding is not None:
                            # Ensure 512 dimensions
                            if len(embedding) != EMBEDDING_SIZE:
                                embedding = fu.resize_embedding_to_512(embedding)
                            
                            embedding_str = base64.b64encode(embedding.tobytes()).decode('utf-8')
                            cursor.execute("""
                                INSERT INTO face_embeddings (student_id, embedding, photo_number)
                                VALUES (?, ?, ?)
                            """, (student_id, embedding_str, i))
                            embeddings_added += 1
                    except Exception as e:
                        logger.warning(f"Failed to process image {i} for student {name}: {e}")
                
                if embeddings_added == 0:
                    # Remove student if no valid embeddings
                    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
                    conn.commit()
                    return False, "No valid face detected in any photo"
            
            conn.commit()
            logger.info(f"Student {name} added with {embeddings_added} photo embeddings")
            return True, f"Student added successfully with {embeddings_added} photos"
            
    except sqlite3.IntegrityError as e:
        if "roll_number" in str(e):
            return False, "Roll number already exists"
        elif "email" in str(e):
            return False, "Email already exists"
        else:
            return False, f"Data integrity error: {str(e)}"
    except Exception as e:
        logger.error(f"Error adding student: {e}")
        return False, f"Error adding student: {str(e)}"

def get_all_students():
    """Get all students with photo count"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, COUNT(fe.id) as photo_count
                FROM students s
                LEFT JOIN face_embeddings fe ON s.id = fe.student_id
                GROUP BY s.id
                ORDER BY s.name
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting students: {e}")
        return []

def delete_student(roll_number):
    """Delete student by roll number (cascade deletes embeddings)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE roll_number = ?", (roll_number,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Student with roll number {roll_number} deleted")
                return True, "Student deleted successfully"
            else:
                return False, "Student not found"
                
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        return False, f"Error deleting student: {str(e)}"

def recognize_student(input_image):
    """Enhanced student recognition with multi-embedding support"""
    try:
        import face_utils as fu
        
        # Generate embedding from input image
        input_embedding = fu.image_to_embedding_bgr(input_image)
        if input_embedding is None:
            return {"success": False, "message": "No face detected in image"}
        
        # Ensure proper dimensions
        if len(input_embedding) != EMBEDDING_SIZE:
            input_embedding = fu.resize_embedding_to_512(input_embedding)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, fe.embedding 
                FROM students s 
                JOIN face_embeddings fe ON s.id = fe.student_id
            """)
            
            results = cursor.fetchall()
            best_match = None
            best_similarity = 0
            recognition_threshold = 0.6
            
            logger.info(f"Comparing against {len(results)} stored embeddings")
            
            for result in results:
                try:
                    result_dict = dict(result)
                    
                    # Decode stored embedding
                    stored_embedding = np.frombuffer(
                        base64.b64decode(result_dict['embedding']), 
                        dtype=np.float32
                    )
                    
                    # Ensure same dimensions
                    if len(stored_embedding) != EMBEDDING_SIZE:
                        stored_embedding = fu.resize_embedding_to_512(stored_embedding)
                    
                    # Calculate similarity
                    similarity = fu.cosine_similarity(input_embedding, stored_embedding)
                    
                    if similarity > best_similarity and similarity > recognition_threshold:
                        best_similarity = similarity
                        best_match = result_dict
                        
                except Exception as e:
                    logger.warning(f"Error processing embedding: {e}")
                    continue
            
            if best_match:
                logger.info(f"Recognition successful: {best_match['name']} ({best_similarity:.3f})")
                return {
                    "success": True,
                    "student": best_match,
                    "confidence": best_similarity * 100
                }
            else:
                logger.warning(f"No match found (best: {best_similarity:.3f}, threshold: {recognition_threshold})")
                return {"success": False, "message": "Student not recognized"}
                
    except Exception as e:
        logger.error(f"Error in recognition: {e}")
        return {"success": False, "message": f"Recognition error: {str(e)}"}

def mark_attendance(student_id, action="AUTO"):
    """Enhanced attendance marking with smart IN/OUT detection"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            today = date.today()
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Get today's attendance record
            cursor.execute("""
                SELECT id, time_in, time_out FROM attendance 
                WHERE student_id = ? AND date = ?
            """, (student_id, today))
            
            existing_record = cursor.fetchone()
            
            if not existing_record:
                # No record exists - mark IN
                cursor.execute("""
                    INSERT INTO attendance (student_id, date, time_in)
                    VALUES (?, ?, ?)
                """, (student_id, today, current_time))
                conn.commit()
                
                logger.info(f"Marked IN for student {student_id} at {current_time}")
                return {"success": True, "message": f"Entry marked at {current_time}"}
            
            else:
                record = dict(existing_record)
                
                if action == "AUTO":
                    # Smart detection based on current status
                    if record['time_in'] and not record['time_out']:
                        # Already IN, mark OUT
                        cursor.execute("""
                            UPDATE attendance SET time_out = ?
                            WHERE student_id = ? AND date = ?
                        """, (current_time, student_id, today))
                        conn.commit()
                        
                        logger.info(f"Marked OUT for student {student_id} at {current_time}")
                        return {"success": True, "message": f"Exit marked at {current_time}"}
                    
                    elif record['time_in'] and record['time_out']:
                        # Already complete - could be re-entry
                        return {"success": False, "message": "Attendance already complete for today"}
                    
                    else:
                        # Mark IN if somehow time_in is missing
                        cursor.execute("""
                            UPDATE attendance SET time_in = ?
                            WHERE student_id = ? AND date = ?
                        """, (current_time, student_id, today))
                        conn.commit()
                        
                        logger.info(f"Marked IN for student {student_id} at {current_time}")
                        return {"success": True, "message": f"Entry marked at {current_time}"}
                
                elif action == "IN":
                    if record['time_in']:
                        return {"success": False, "message": "Entry already marked today"}
                    else:
                        cursor.execute("""
                            UPDATE attendance SET time_in = ?
                            WHERE student_id = ? AND date = ?
                        """, (current_time, student_id, today))
                        conn.commit()
                        return {"success": True, "message": f"Entry marked at {current_time}"}
                
                elif action == "OUT":
                    if not record['time_in']:
                        return {"success": False, "message": "Cannot mark exit before entry"}
                    elif record['time_out']:
                        return {"success": False, "message": "Exit already marked today"}
                    else:
                        cursor.execute("""
                            UPDATE attendance SET time_out = ?
                            WHERE student_id = ? AND date = ?
                        """, (current_time, student_id, today))
                        conn.commit()
                        return {"success": True, "message": f"Exit marked at {current_time}"}
            
            return {"success": False, "message": "Unexpected error in attendance marking"}
            
    except Exception as e:
        logger.error(f"Error marking attendance: {e}")
        return {"success": False, "message": f"Error marking attendance: {str(e)}"}

def get_attendance_records(start_date=None, end_date=None):
    """Get attendance records with date filtering"""
    try:
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id as student_id, s.name, s.roll_number, s.course, 
                       a.date, a.time_in, a.time_out
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date BETWEEN ? AND ?
                ORDER BY a.date DESC, a.time_in DESC
            """, (start_date, end_date))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Error getting attendance records: {e}")
        return []

def get_today_stats():
    """Get comprehensive today's statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            today = date.today()
            
            # Total students
            cursor.execute("SELECT COUNT(*) as count FROM students")
            total_students = cursor.fetchone()['count']
            
            # Present today (students who marked IN)
            cursor.execute("""
                SELECT COUNT(*) as count FROM attendance 
                WHERE date = ? AND time_in IS NOT NULL
            """, (today,))
            present_today = cursor.fetchone()['count']
            
            # Calculate absent and attendance rate
            absent_today = total_students - present_today
            attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0
            
            return {
                'total_students': total_students,
                'present_today': present_today,
                'absent_today': absent_today,
                'attendance_rate': attendance_rate
            }
            
    except Exception as e:
        logger.error(f"Error getting today's stats: {e}")
        return {
            'total_students': 0,
            'present_today': 0,
            'absent_today': 0,
            'attendance_rate': 0
        }

# ---------------- Database Utilities (fixed) ----------------
def get_attendance_analytics():
    """Get comprehensive attendance analytics with correct handling of absent days."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # define date range used across analytics (last 30 days)
            # change this if you want a different window
            start_date_sql = "date('now', '-30 days')"

            # 1) Daily attendance for last 30 days (present only)
            cursor.execute(f"""
                SELECT date, COUNT(*) as count
                FROM attendance
                WHERE date >= {start_date_sql} AND time_in IS NOT NULL
                GROUP BY date
                ORDER BY date
            """)
            daily_attendance = [dict(row) for row in cursor.fetchall()]

            # 2) Course-level totals: total_students, total_classes (unique dates), total_present_records
            # total_present_records = total present events (student x date) in window
            cursor.execute(f"""
                SELECT s.course,
                       COUNT(DISTINCT s.id) as total_students,
                       COUNT(DISTINCT a.date) as total_classes,
                       SUM(CASE WHEN a.time_in IS NOT NULL THEN 1 ELSE 0 END) as total_present_records
                FROM students s
                LEFT JOIN attendance a
                  ON s.id = a.student_id AND a.date >= {start_date_sql}
                GROUP BY s.course
            """)
            course_rows = cursor.fetchall()

            course_attendance = []
            # build a map course -> total_classes for easy lookup when computing student %s
            course_total_classes = {}
            for row in course_rows:
                course = row['course']
                total_students = row['total_students'] or 0
                total_classes = (row['total_classes'] or 0)
                total_present_records = (row['total_present_records'] or 0)

                # compute attendance_rate as fraction of filled seats over total seats
                denom = total_classes * total_students
                if denom > 0:
                    attendance_rate = (total_present_records / denom) * 100
                else:
                    attendance_rate = 0.0

                course_attendance.append({
                    'course': course,
                    'total_students': total_students,
                    'present_records': total_present_records,
                    'total_classes': total_classes,
                    'attendance_rate': min(round(attendance_rate, 1), 100)
                })

                course_total_classes[course] = total_classes

            # 3) Student present_days (count distinct dates student was present) in the same date window
            cursor.execute(f"""
                SELECT student_id, COUNT(DISTINCT date) as present_days
                FROM attendance
                WHERE date >= {start_date_sql} AND time_in IS NOT NULL
                GROUP BY student_id
            """)
            present_rows = cursor.fetchall()
            present_map = {r['student_id']: r['present_days'] for r in present_rows}

            # 4) Build student list and compute attendance % using course_total_classes as denominator
            cursor.execute("SELECT id, name, roll_number, course FROM students")
            students = cursor.fetchall()

            student_attendance = []
            for s in students:
                sid = s['id']
                course = s['course']
                present_days = present_map.get(sid, 0)
                total_classes = course_total_classes.get(course, 0)

                if total_classes > 0:
                    attendance_percentage = (present_days / total_classes) * 100
                else:
                    # No classes conducted in window for this course → show 0% (or choose None/NA)
                    attendance_percentage = 0.0

                student_attendance.append({
                    'student_id': sid,
                    'name': s['name'],
                    'roll_number': s['roll_number'],
                    'course': course,
                    'present_days': present_days,
                    'total_days': total_classes,               # total possible days for that student
                    'attendance_percentage': min(round(attendance_percentage, 1), 100)
                })

            return {
                'daily_attendance': daily_attendance,
                'student_attendance': student_attendance,
                'course_attendance': course_attendance
            }

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {}


# ---------------- Additional Utility Functions ----------------
def get_course_wise_stats():
    """Get statistics by course"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT course, COUNT(*) as student_count
                FROM students 
                GROUP BY course
                ORDER BY student_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting course stats: {e}")
        return []


def get_peak_hours():
    """Analyze peak attendance hours"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT substr(time_in, 1, 2) as hour, COUNT(*) as count
                FROM attendance 
                WHERE time_in IS NOT NULL
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 5
            """)
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting peak hours: {e}")
        return []


logger.info("Enhanced database module loaded with dual attendance tracking")

def delete_all_students():
    """Delete all student records and their embeddings"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students")  # CASCADE will delete embeddings and attendance
            conn.commit()
            logger.info("All student records deleted")
            return True, "All students deleted successfully"
            
    except Exception as e:
        logger.error(f"Error deleting all students: {e}")
        return False, f"Error deleting students: {str(e)}"

def delete_all_users_except_admin():
    """Delete all users except admin accounts"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE role != 'admin'")
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted_count} non-admin user accounts")
            return True, f"Deleted {deleted_count} user accounts"
            
    except Exception as e:
        logger.error(f"Error deleting users: {e}")
        return False, f"Error deleting users: {str(e)}"

