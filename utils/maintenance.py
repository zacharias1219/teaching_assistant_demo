from datetime import datetime, timedelta
from typing import Dict, List
from utils.database import db_manager
import os

class MaintenanceManager:
    def __init__(self):
        pass
    
    def cleanup_expired_files(self) -> Dict:
        """Clean up files older than 7 days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Find expired files using SQLite
            expired_files = db_manager.execute_query(
                "SELECT * FROM files WHERE upload_date < ?",
                (cutoff_date,),
                fetch_all=True
            ) or []
            
            deleted_count = 0
            errors = []
            
            for file_doc in expired_files:
                try:
                    db_manager.fs.delete(file_doc["_id"])
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"Failed to delete {file_doc.get('filename', 'unknown')}: {e}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "total_expired": len(expired_files),
                "errors": errors
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Cleanup failed: {e}",
                "deleted_count": 0,
                "total_expired": 0,
                "errors": []
            }
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            # File statistics
            total_files = db_manager.db.fs.files.count_documents({})
            
            # Storage size (approximate)
            files_cursor = db_manager.db.fs.files.find({}, {"length": 1})
            total_size = sum(file_doc.get("length", 0) for file_doc in files_cursor)
            
            # Recent files (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_files = db_manager.db.fs.files.count_documents({
                "upload_date": {"$gte": recent_cutoff}
            })
            
            # Old files (older than 7 days)
            old_files = db_manager.db.fs.files.count_documents({
                "upload_date": {"$lt": recent_cutoff}
            })
            
            return {
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "recent_files": recent_files,
                "old_files": old_files,
                "storage_healthy": old_files < 100  # Flag if too many old files
            }
            
        except Exception as e:
            return {
                "total_files": 0,
                "total_size_mb": 0,
                "recent_files": 0,
                "old_files": 0,
                "storage_healthy": False,
                "error": str(e)
            }
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        try:
            from utils.student_manager import student_manager
            from utils.test_manager import test_manager
            from utils.submission_manager import submission_manager
            from utils.ai_grading import ai_grading_manager
            
            # Database connectivity
            try:
                db_manager.client.admin.command('ping')
                db_healthy = True
                db_error = None
            except Exception as e:
                db_healthy = False
                db_error = str(e)
            
            # OpenAI API connectivity
            ai_healthy = ai_grading_manager.test_api_connection()
            
            # Data counts
            students_count = len(student_manager.get_all_students())
            tests_count = len(test_manager.get_all_tests())
            submissions_count = len(submission_manager.get_all_submissions())
            
            # Grading statistics
            submissions = submission_manager.get_all_submissions()
            graded_count = len([s for s in submissions if s.get('graded', False)])
            pending_count = submissions_count - graded_count
            
            # Storage stats
            storage_stats = self.get_storage_stats()
            
            return {
                "timestamp": datetime.utcnow(),
                "database": {
                    "healthy": db_healthy,
                    "error": db_error
                },
                "ai_service": {
                    "healthy": ai_healthy
                },
                "data_counts": {
                    "students": students_count,
                    "tests": tests_count,
                    "submissions": submissions_count,
                    "graded": graded_count,
                    "pending": pending_count
                },
                "storage": storage_stats,
                "overall_healthy": db_healthy and ai_healthy and storage_stats.get("storage_healthy", True)
            }
            
        except Exception as e:
            return {
                "timestamp": datetime.utcnow(),
                "error": str(e),
                "overall_healthy": False
            }
    
    def export_data(self, collection_name: str) -> List[Dict]:
        """Export data from a collection"""
        try:
            collection = db_manager.get_collection(collection_name)
            data = list(collection.find({}, {"_id": 0}))
            return data
        except Exception as e:
            print(f"Error exporting {collection_name}: {e}")
            return []
    
    def get_activity_summary(self, days: int = 7) -> Dict:
        """Get activity summary for the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Recent submissions
            submissions_collection = db_manager.get_collection('submissions')
            recent_submissions = submissions_collection.count_documents({
                "date": {"$gte": cutoff_date}
            })
            
            # Recent tests
            tests_collection = db_manager.get_collection('tests')
            recent_tests = tests_collection.count_documents({
                "created_at": {"$gte": cutoff_date}
            })
            
            # Recent students
            students_collection = db_manager.get_collection('students')
            recent_students = students_collection.count_documents({
                "created_at": {"$gte": cutoff_date}
            })
            
            return {
                "period_days": days,
                "recent_submissions": recent_submissions,
                "recent_tests": recent_tests,
                "recent_students": recent_students,
                "total_activity": recent_submissions + recent_tests + recent_students
            }
            
        except Exception as e:
            return {
                "period_days": days,
                "recent_submissions": 0,
                "recent_tests": 0,
                "recent_students": 0,
                "total_activity": 0,
                "error": str(e)
            }

# Global maintenance manager instance
maintenance_manager = MaintenanceManager()
