"""
Attendance management business logic
Extracted from db.py attendance functions
"""
import logging
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime, timedelta
from database.attendance_repository import AttendanceRepository
from services.student_service import StudentService

logger = logging.getLogger(__name__)

class AttendanceService:
    """Business logic for attendance management"""
    
    def __init__(self):
        self.attendance_repo = AttendanceRepository()
        self.student_service = StudentService()
    
    def mark_attendance_by_recognition(self, image, marked_by: str = 'system') -> Tuple[bool, str, Optional[Dict]]:
        """Mark attendance using face recognition"""
        try:
            # Recognize student from image
            is_recognized, student_info, confidence = self.student_service.recognize_student(image)
            
            if not is_recognized:
                return False, f"Face not recognized. Confidence: {confidence:.2f}", None
            
            # Mark attendance
            success, message = self.attendance_repo.mark_attendance(
                student_info['student_id'], 'present', marked_by
            )
            
            # Add confidence to student info
            student_info['recognition_confidence'] = confidence
            
            return success, message, student_info
            
        except Exception as e:
            logger.error(f"Error marking attendance by recognition: {e}")
            return False, f"Error marking attendance: {str(e)}", None
    
    def mark_attendance_manual(self, student_id: int, status: str = 'present', 
                             marked_by: str = 'manual') -> Tuple[bool, str]:
        """Manually mark attendance for a student"""
        return self.attendance_repo.mark_attendance(student_id, status, marked_by)
    
    def get_attendance_records(self, start_date: date = None, end_date: date = None, 
                             student_id: int = None) -> List[Dict]:
        """Get attendance records with filters"""
        return self.attendance_repo.get_attendance_records(start_date, end_date, student_id)
    
    def get_today_attendance_summary(self) -> Dict:
        """Get today's attendance summary"""
        return self.attendance_repo.get_today_stats()
    
    def get_attendance_analytics(self, days: int = 30) -> Dict:
        """Get attendance analytics"""
        return self.attendance_repo.get_attendance_analytics(days)
    
    def get_student_attendance_report(self, student_id: int, days: int = 30) -> Dict:
        """Get detailed attendance report for a specific student"""
        try:
            # Get student info
            student = self.student_service.get_student_by_id(student_id)
            if not student:
                return {}
            
            # Get attendance records for the student
            start_date = date.today() - timedelta(days=days)
            records = self.attendance_repo.get_attendance_records(
                start_date=start_date, student_id=student_id
            )
            
            # Calculate statistics
            total_days = days
            present_days = len([r for r in records if r['status'] == 'present'])
            absent_days = total_days - present_days
            attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            
            # Time analysis
            time_in_records = [r for r in records if r['time_in']]
            time_out_records = [r for r in records if r['time_out']]
            
            return {
                'student_info': student,
                'period_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'attendance_rate': round(attendance_rate, 1),
                'records': records,
                'has_time_in': len(time_in_records),
                'has_time_out': len(time_out_records)
            }
            
        except Exception as e:
            logger.error(f"Error getting student attendance report: {e}")
            return {}
    
    def get_course_attendance_summary(self, course: str, days: int = 30) -> Dict:
        """Get attendance summary for a specific course"""
        try:
            # Get students in the course
            course_students = self.student_service.get_students_by_course(course)
            
            if not course_students:
                return {
                    'course': course,
                    'total_students': 0,
                    'attendance_data': []
                }
            
            # Get attendance data for each student
            start_date = date.today() - timedelta(days=days)
            attendance_data = []
            
            for student in course_students:
                records = self.attendance_repo.get_attendance_records(
                    start_date=start_date, student_id=student['id']
                )
                
                present_days = len([r for r in records if r['status'] == 'present'])
                attendance_rate = (present_days / days * 100) if days > 0 else 0
                
                attendance_data.append({
                    'student_id': student['id'],
                    'student_name': student['name'],
                    'roll_number': student['roll_number'],
                    'present_days': present_days,
                    'attendance_rate': round(attendance_rate, 1)
                })
            
            # Calculate course statistics
            total_students = len(course_students)
            avg_attendance = sum(s['attendance_rate'] for s in attendance_data) / total_students if total_students > 0 else 0
            
            return {
                'course': course,
                'total_students': total_students,
                'average_attendance_rate': round(avg_attendance, 1),
                'attendance_data': attendance_data
            }
            
        except Exception as e:
            logger.error(f"Error getting course attendance summary: {e}")
            return {
                'course': course,
                'total_students': 0,
                'attendance_data': []
            }
    
    def get_daily_attendance_trends(self, days: int = 30) -> List[Dict]:
        """Get daily attendance trends"""
        try:
            analytics = self.attendance_repo.get_attendance_analytics(days)
            return analytics.get('daily_attendance', [])
        except Exception as e:
            logger.error(f"Error getting daily trends: {e}")
            return []
    
    def get_peak_attendance_hours(self, days: int = 30) -> Dict:
        """Analyze peak attendance hours"""
        try:
            records = self.attendance_repo.get_attendance_records(
                start_date=date.today() - timedelta(days=days)
            )
            
            hour_counts = {}
            
            for record in records:
                if record['time_in']:
                    try:
                        # Extract hour from time_in
                        time_str = record['time_in']
                        if isinstance(time_str, str):
                            hour = datetime.fromisoformat(time_str).hour
                        else:
                            hour = time_str.hour
                        
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1
                    except:
                        continue
            
            # Find peak hour
            peak_hour = max(hour_counts.keys(), key=lambda k: hour_counts[k]) if hour_counts else None
            
            return {
                'hourly_distribution': hour_counts,
                'peak_hour': peak_hour,
                'peak_hour_count': hour_counts.get(peak_hour, 0) if peak_hour else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing peak hours: {e}")
            return {
                'hourly_distribution': {},
                'peak_hour': None,
                'peak_hour_count': 0
            }
    
    def export_attendance_data(self, start_date: date = None, end_date: date = None) -> List[Dict]:
        """Export attendance data for CSV/Excel"""
        try:
            records = self.attendance_repo.get_attendance_records(start_date, end_date)
            
            # Format for export
            export_data = []
            for record in records:
                export_data.append({
                    'Date': record['date'],
                    'Student Name': record['student_name'],
                    'Roll Number': record['roll_number'],
                    'Time In': record['time_in'],
                    'Time Out': record['time_out'],
                    'Status': record['status'],
                    'Marked By': record['marked_by']
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting attendance data: {e}")
            return []
