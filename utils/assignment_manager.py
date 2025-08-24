from datetime import datetime, timedelta
from typing import List, Dict
from utils.database import db_manager
from utils.test_manager import test_manager
from utils.student_manager import student_manager

class AssignmentManager:
    """
    Manages test assignments to students.
    For this simple PoC, all tests are assigned to all students.
    Future versions could have more sophisticated assignment logic.
    """
    
    def __init__(self):
        pass
    
    def get_assigned_tests(self, student_id: str) -> List[Dict]:
        """
        Get tests assigned to a specific student.
        For now, all active tests are assigned to all students.
        """
        try:
            # Get all tests (in real app, this would be filtered by assignments)
            all_tests = test_manager.get_all_tests()
            
            # Filter to show only current and future tests (not past tests)
            now = datetime.utcnow()
            cutoff_date = now - timedelta(days=30)  # Show tests from last 30 days
            
            assigned_tests = []
            for test in all_tests:
                # Include tests that are not too old
                if test['date'] >= cutoff_date:
                    assigned_tests.append(test)
            
            return assigned_tests
            
        except Exception as e:
            print(f"Error getting assigned tests: {e}")
            return []
    
    def is_test_assigned(self, test_id: str, student_id: str) -> bool:
        """
        Check if a specific test is assigned to a student.
        For now, all tests are assigned to all students.
        """
        try:
            test = test_manager.get_test_by_id(test_id)
            if not test:
                return False
            
            # Simple logic: all tests are assigned to all students
            # In future, this could check an assignments table
            return True
            
        except Exception as e:
            print(f"Error checking test assignment: {e}")
            return False
    
    def assign_test_to_student(self, test_id: str, student_id: str) -> bool:
        """
        Assign a test to a student.
        For this PoC, this is a placeholder (all tests auto-assigned).
        """
        # Placeholder for future assignment logic
        # Could store in an 'assignments' collection
        return True
    
    def assign_test_to_class(self, test_id: str, class_name: str) -> bool:
        """
        Assign a test to all students in a class.
        Placeholder for future functionality.
        """
        try:
            students = student_manager.get_students_by_class(class_name)
            for student in students:
                self.assign_test_to_student(test_id, student['student_id'])
            return True
        except Exception as e:
            print(f"Error assigning test to class: {e}")
            return False
    
    def get_assignment_stats(self, test_id: str) -> Dict:
        """Get assignment statistics for a test"""
        try:
            from utils.submission_manager import submission_manager
            
            # For now, assume all students are assigned
            all_students = student_manager.get_all_students()
            total_assigned = len(all_students)
            
            # Count submissions
            submissions = submission_manager.get_submissions_by_test(test_id)
            total_submitted = len(submissions)
            
            return {
                "total_assigned": total_assigned,
                "total_submitted": total_submitted,
                "pending": total_assigned - total_submitted,
                "submission_rate": (total_submitted / total_assigned * 100) if total_assigned > 0 else 0
            }
        except Exception as e:
            print(f"Error getting assignment stats: {e}")
            return {"total_assigned": 0, "total_submitted": 0, "pending": 0, "submission_rate": 0}

# Global assignment manager instance
assignment_manager = AssignmentManager()
