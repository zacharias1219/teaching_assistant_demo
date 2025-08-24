import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
from utils.database import db_manager

class SubmissionManager:
    def __init__(self):
        pass  # No need for collection reference in SQLite
    
    def create_submission(self, test_id: str, student_id: str, answers: str = "",
                         status: str = "submitted") -> bool:
        """Create a new submission"""
        try:
            # Check for duplicate submission
            existing = db_manager.execute_query(
                "SELECT submission_id FROM submissions WHERE test_id = ? AND student_id = ?",
                (test_id, student_id),
                fetch_one=True
            )
            
            if existing:
                return False  # Duplicate submission not allowed
            
            submission_id = str(uuid.uuid4())
            db_manager.execute_query(
                """INSERT INTO submissions (submission_id, test_id, student_id, answers, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                (submission_id, test_id, student_id, answers, status)
            )
            
            return True
            
        except Exception as e:
            print(f"Error creating submission: {e}")
            return False
    
    def get_submissions_by_test(self, test_id: str) -> List[Dict]:
        """Get all submissions for a specific test"""
        try:
            submissions = db_manager.execute_query(
                "SELECT * FROM submissions WHERE test_id = ? ORDER BY submitted_at DESC",
                (test_id,),
                fetch_all=True
            )
            return submissions or []
        except Exception as e:
            print(f"Error fetching submissions by test: {e}")
            return []
    
    def get_submissions_by_student(self, student_id: str) -> List[Dict]:
        """Get all submissions by a specific student"""
        try:
            submissions = db_manager.execute_query(
                "SELECT * FROM submissions WHERE student_id = ? ORDER BY submitted_at DESC",
                (student_id,),
                fetch_all=True
            )
            return submissions or []
        except Exception as e:
            print(f"Error fetching submissions by student: {e}")
            return []
    
    def get_submission_by_id(self, submission_id: str) -> Optional[Dict]:
        """Get submission by ID"""
        try:
            submission = db_manager.execute_query(
                "SELECT * FROM submissions WHERE submission_id = ?",
                (submission_id,),
                fetch_one=True
            )
            return submission
        except Exception as e:
            print(f"Error fetching submission: {e}")
            return None
    
    def get_submission(self, test_id: str, student_id: str) -> Optional[Dict]:
        """Get specific submission by test and student"""
        try:
            submission = db_manager.execute_query(
                "SELECT * FROM submissions WHERE test_id = ? AND student_id = ?",
                (test_id, student_id),
                fetch_one=True
            )
            return submission
        except Exception as e:
            print(f"Error fetching submission: {e}")
            return None
    
    def update_submission_grading(self, submission_id: str, score: int, max_score: int, 
                                feedback: str = "") -> bool:
        """Update submission with grading results"""
        try:
            db_manager.execute_query(
                """UPDATE submissions SET score = ?, max_score = ?, feedback = ?, 
                   graded_at = ?, status = 'graded' WHERE submission_id = ?""",
                (score, max_score, feedback, datetime.now(), submission_id)
            )
            return True
        except Exception as e:
            print(f"Error updating submission grading: {e}")
            return False
    
    def delete_submission(self, submission_id: str) -> bool:
        """Delete a submission"""
        try:
            db_manager.execute_query(
                "DELETE FROM submissions WHERE submission_id = ?",
                (submission_id,)
            )
            return True
        except Exception as e:
            print(f"Error deleting submission: {e}")
            return False
    
    def get_all_submissions(self) -> List[Dict]:
        """Get all submissions (admin view)"""
        try:
            submissions = db_manager.execute_query(
                "SELECT * FROM submissions ORDER BY submitted_at DESC",
                fetch_all=True
            )
            return submissions or []
        except Exception as e:
            print(f"Error fetching all submissions: {e}")
            return []
    
    def has_student_submitted(self, test_id: str, student_id: str) -> bool:
        """Check if student has already submitted for a test"""
        try:
            submission = db_manager.execute_query(
                "SELECT submission_id FROM submissions WHERE test_id = ? AND student_id = ?",
                (test_id, student_id),
                fetch_one=True
            )
            return submission is not None
        except Exception as e:
            print(f"Error checking submission status: {e}")
            return False
    
    def get_submission_count(self) -> int:
        """Get total number of submissions"""
        try:
            result = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM submissions",
                fetch_one=True
            )
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error fetching submission count: {e}")
            return 0

# Global submission manager instance
submission_manager = SubmissionManager()
