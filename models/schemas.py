from datetime import datetime
from typing import Optional, List, Dict, Any

class User:
    def __init__(self, user_id: str, username: str, password_hash: str, role: str):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role  # "admin" or "student"

class Student:
    def __init__(self, student_id: str, name: str, class_name: str):
        self.student_id = student_id
        self.name = name
        self.class_name = class_name

class Test:
    def __init__(self, test_id: str, title: str, subject: str, date: datetime, 
                 rubric: Optional[str] = None, file_id: Optional[str] = None):
        self.test_id = test_id
        self.title = title
        self.subject = subject
        self.date = date
        self.rubric = rubric
        self.file_id = file_id  # GridFS file ID

class Submission:
    def __init__(self, submission_id: str, test_id: str, student_id: str, 
                 date: datetime, file_id: str, total_score: Optional[float] = None,
                 per_question_scores: Optional[List[Dict]] = None,
                 remarks: Optional[str] = None, strengths: Optional[str] = None,
                 improvements: Optional[str] = None, rubric_filled: Optional[str] = None):
        self.submission_id = submission_id
        self.test_id = test_id
        self.student_id = student_id
        self.date = date
        self.file_id = file_id
        self.total_score = total_score
        self.per_question_scores = per_question_scores or []
        self.remarks = remarks
        self.strengths = strengths
        self.improvements = improvements
        self.rubric_filled = rubric_filled

class Settings:
    def __init__(self, prompt_type: str, prompt_text: str):
        self.prompt_type = prompt_type  # "ocr" or "grading"
        self.prompt_text = prompt_text
