"""
Database migration utilities
Handle schema changes and data preservation
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any
from database.connection import get_db_connection
from utils.backup_manager import BackupManager
from config.database import TABLE_SCHEMAS, DATABASE_INDEXES

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Handle database migrations and schema updates"""
    
    def __init__(self, db_path: str = "data/attendance.db"):
        self.db_path = Path(db_path)
        self.backup_manager = BackupManager(str(db_path))
    
    def migrate_from_old_system(self, old_db_path: str) -> bool:
        """Migrate data from old database system"""
        try:
            old_db = Path(old_db_path)
            if not old_db.exists():
                logger.warning(f"Old database not found: {old_db_path}")
                return False
            
            # Create backup of current database
            self.backup_manager.create_backup("pre_migration_backup.db")
            
            # Export data from old database
            old_data = self._export_old_data(old_db_path)
            
            # Import into new database
            success = self._import_migrated_data(old_data)
            
            if success:
                logger.info("Migration completed successfully")
                return True
            else:
                logger.error("Migration failed")
                return False
                
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return False
    
    def _export_old_data(self, old_db_path: str) -> Dict[str, Any]:
        """Export data from old database format"""
        try:
            with sqlite3.connect(old_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                data = {}
                
                # Check which tables exist in old database
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table}")
                        data[table] = [dict(row) for row in cursor.fetchall()]
                        logger.info(f"Exported {len(data[table])} records from {table}")
                    except Exception as e:
                        logger.warning(f"Could not export table {table}: {e}")
                
                return data
                
        except Exception as e:
            logger.error(f"Old data export failed: {e}")
            return {}
    
    def _import_migrated_data(self, old_data: Dict[str, Any]) -> bool:
        """Import migrated data into new database structure"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Map old table structure to new structure
                table_mappings = {
                    'users': self._migrate_users,
                    'students': self._migrate_students,
                    'face_embeddings': self._migrate_face_embeddings,
                    'attendance': self._migrate_attendance
                }
                
                for old_table, migration_func in table_mappings.items():
                    if old_table in old_data:
                        success = migration_func(cursor, old_data[old_table])
                        if not success:
                            logger.warning(f"Migration of {old_table} had issues")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Data import failed: {e}")
            return False
    
    def _migrate_users(self, cursor, users_data: List[Dict]) -> bool:
        """Migrate users table"""
        try:
            for user in users_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (username, email, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user.get('username', user.get('email', 'unknown')),
                    user.get('email'),
                    user.get('password_hash', user.get('password')),
                    user.get('role', 'user'),
                    user.get('created_at', user.get('created_date'))
                ))
            logger.info(f"Migrated {len(users_data)} users")
            return True
        except Exception as e:
            logger.error(f"User migration failed: {e}")
            return False
    
    def _migrate_students(self, cursor, students_data: List[Dict]) -> bool:
        """Migrate students table"""
        try:
            for student in students_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO students 
                    (name, roll_number, email, phone, course, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    student.get('name'),
                    student.get('roll_number'),
                    student.get('email'),
                    student.get('phone'),
                    student.get('course'),
                    student.get('created_at'),
                    student.get('is_active', 1)
                ))
            logger.info(f"Migrated {len(students_data)} students")
            return True
        except Exception as e:
            logger.error(f"Student migration failed: {e}")
            return False
    
    def _migrate_face_embeddings(self, cursor, embeddings_data: List[Dict]) -> bool:
        """Migrate face embeddings table"""
        try:
            for embedding in embeddings_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO face_embeddings
                    (student_id, embedding_data, photo_id, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    embedding.get('student_id'),
                    embedding.get('embedding_data'),
                    embedding.get('photo_id'),
                    embedding.get('created_at')
                ))
            logger.info(f"Migrated {len(embeddings_data)} face embeddings")
            return True
        except Exception as e:
            logger.error(f"Face embeddings migration failed: {e}")
            return False
    
    def _migrate_attendance(self, cursor, attendance_data: List[Dict]) -> bool:
        """Migrate attendance table"""
        try:
            for record in attendance_data:
                cursor.execute('''
                    INSERT OR REPLACE INTO attendance
                    (student_id, date, time_in, time_out, status, marked_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('student_id'),
                    record.get('date'),
                    record.get('time_in'),
                    record.get('time_out'),
                    record.get('status', 'present'),
                    record.get('marked_by', 'system'),
                    record.get('created_at')
                ))
            logger.info(f"Migrated {len(attendance_data)} attendance records")
            return True
        except Exception as e:
            logger.error(f"Attendance migration failed: {e}")
            return False

def migrate_from_old_database(old_db_path: str) -> bool:
    """Convenience function for migration"""
    migration = DatabaseMigration()
    return migration.migrate_from_old_system(old_db_path)
