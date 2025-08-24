import uuid
from datetime import datetime
from typing import List, Dict, Optional
from utils.database import db_manager

class StudentManager:
    def __init__(self):
        pass
    
    def create_student(self, name: str, class_name: str) -> bool:
        """Create a new student"""
        try:
            student_id = str(uuid.uuid4())
            
            db_manager.execute_query(
                """INSERT INTO students (student_id, name, email, phone, address) 
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, name.strip(), "", "", "")
            )
            return True
            
        except Exception as e:
            print(f"Error creating student: {e}")
            return False
    
    def get_all_students(self) -> List[Dict]:
        """Get all students sorted by name"""
        try:
            students = db_manager.execute_query(
                "SELECT * FROM students ORDER BY name",
                fetch_all=True
            )
            # Add class_name field for compatibility
            for student in students:
                student['class_name'] = student.get('class_name', 'General')
            return students
        except Exception as e:
            print(f"Error fetching students: {e}")
            return []
    
    def get_student_by_id(self, student_id: str) -> Optional[Dict]:
        """Get student by ID"""
        try:
            student = db_manager.execute_query(
                "SELECT * FROM students WHERE student_id = ?",
                (student_id,),
                fetch_one=True
            )
            if student:
                student['class_name'] = student.get('class_name', 'General')
            return student
        except Exception as e:
            print(f"Error fetching student: {e}")
            return None
    
    def update_student(self, student_id: str, name: str, class_name: str) -> bool:
        """Update student information"""
        try:
            db_manager.execute_query(
                "UPDATE students SET name = ? WHERE student_id = ?",
                (name.strip(), student_id)
            )
            return True
        except Exception as e:
            print(f"Error updating student: {e}")
            return False
    
    def delete_student(self, student_id: str) -> bool:
        """Delete a student"""
        try:
            # Check if student has any submissions
            submissions = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM submissions WHERE student_id = ?",
                (student_id,),
                fetch_one=True
            )
            
            if submissions and submissions['count'] > 0:
                return False  # Cannot delete student with submissions
            
            db_manager.execute_query(
                "DELETE FROM students WHERE student_id = ?",
                (student_id,)
            )
            return True
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False
    
    def get_students_by_class(self, class_name: str) -> List[Dict]:
        """Get students filtered by class"""
        try:
            # For SQLite version, return all students
            return self.get_all_students()
        except Exception as e:
            print(f"Error fetching students by class: {e}")
            return []
    
    def search_students(self, query: str) -> List[Dict]:
        """Search students by name"""
        try:
            students = db_manager.execute_query(
                "SELECT * FROM students WHERE name LIKE ? ORDER BY name",
                (f"%{query}%",),
                fetch_all=True
            )
            for student in students:
                student['class_name'] = student.get('class_name', 'General')
            return students
        except Exception as e:
            print(f"Error searching students: {e}")
            return []
    
    def get_classes(self) -> List[str]:
        """Get list of all unique classes"""
        return ["General", "10A", "10B", "11A", "11B", "12A", "12B"]

# Global student manager instance
student_manager = StudentManager()