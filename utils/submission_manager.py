import uuid
from datetime import datetime
from typing import List, Dict, Optional
from utils.database import db_manager

class SubmissionManager:
    def __init__(self):
        pass
    
    def create_submission(self, test_id: str, student_id: str, file_data: bytes, 
                         filename: str, content_type: str = None) -> bool:
        """Create a new submission"""
        try:
            # Check for duplicate submission
            existing = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM submissions WHERE test_id = ? AND student_id = ?",
                (test_id, student_id),
                fetch_one=True
            )
            
            if existing and existing['count'] > 0:
                return False  # Duplicate submission not allowed
            
            # Store file
            file_id = db_manager.store_file(file_data, filename, content_type)
            
            submission_id = str(uuid.uuid4())
            
            db_manager.execute_query(
                """INSERT INTO submissions (submission_id, test_id, student_id, answers, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                (submission_id, test_id, student_id, file_id, 'submitted')
            )
            
            # Trigger AI grading asynchronously
            self._trigger_ai_grading(submission_id)
            
            return True
            
        except Exception as e:
            print(f"Error creating submission: {e}")
            return False
    
    def _trigger_ai_grading(self, submission_id: str):
        """Trigger AI grading for a submission with advanced OCR processing"""
        try:
            import threading
            from utils.ai_grading import ai_grading_manager
            from utils.image_processor import image_processor
            
            def grade_async():
                try:
                    # Get submission for advanced processing
                    submission = self.get_submission_by_id(submission_id)
                    if not submission:
                        print(f"Submission {submission_id} not found for grading")
                        return
                    
                    # Get answer file
                    answer_file = self.get_submission_file(submission_id)
                    if not answer_file:
                        print(f"Answer file not found for submission {submission_id}")
                        return
                    
                    # Preprocess answer image for better OCR
                    answer_data = answer_file.read()
                    processed_images = image_processor.preprocess_image(answer_data)
                    
                    # Extract answers by region for better accuracy
                    all_answers = []
                    for i, processed_image in enumerate(processed_images):
                        answers_result = ai_grading_manager.extract_answers_by_region(
                            processed_image,
                            f"Extract answers from page {i+1}. Include all written work, calculations, and final answers."
                        )
                        all_answers.extend(answers_result)
                    
                    # Perform grading with extracted answers
                    result = ai_grading_manager.grade_with_retry(submission_id)
                    if result.get("success"):
                        print(f"✅ Advanced grading completed for submission {submission_id}")
                    else:
                        print(f"❌ Advanced grading failed for submission {submission_id}: {result.get('error')}")
                        
                except Exception as e:
                    print(f"❌ Advanced AI grading error for {submission_id}: {e}")
            
            # Start grading in background thread
            thread = threading.Thread(target=grade_async, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Error triggering AI grading: {e}")
    
    def get_submissions_by_student(self, student_id: str) -> List[Dict]:
        """Get all submissions for a student"""
        try:
            submissions = db_manager.execute_query(
                "SELECT * FROM submissions WHERE student_id = ? ORDER BY submitted_at DESC",
                (student_id,),
                fetch_all=True
            )
            
            # Convert to expected format
            for submission in submissions:
                submission['submission_id'] = submission['submission_id']
                submission['date'] = datetime.fromisoformat(submission['submitted_at'])
                submission['file_id'] = submission['answers']
                submission['graded'] = submission['status'] == 'graded'
                submission['total_score'] = submission.get('score', 0)
                submission['per_question_scores'] = []
                submission['remarks'] = submission.get('feedback', '')
                submission['strengths'] = ''
                submission['improvements'] = ''
                submission['grading_date'] = datetime.fromisoformat(submission['graded_at']) if submission.get('graded_at') else None
            
            return submissions
        except Exception as e:
            print(f"Error fetching student submissions: {e}")
            return []
    
    def get_submissions_by_test(self, test_id: str) -> List[Dict]:
        """Get all submissions for a test"""
        try:
            submissions = db_manager.execute_query(
                "SELECT * FROM submissions WHERE test_id = ? ORDER BY submitted_at DESC",
                (test_id,),
                fetch_all=True
            )
            
            for submission in submissions:
                submission['submission_id'] = submission['submission_id']
                submission['date'] = datetime.fromisoformat(submission['submitted_at'])
                submission['file_id'] = submission['answers']
                submission['graded'] = submission['status'] == 'graded'
                submission['total_score'] = submission.get('score', 0)
                submission['per_question_scores'] = []
                submission['remarks'] = submission.get('feedback', '')
                submission['strengths'] = ''
                submission['improvements'] = ''
                submission['grading_date'] = datetime.fromisoformat(submission['graded_at']) if submission.get('graded_at') else None
            
            return submissions
        except Exception as e:
            print(f"Error fetching test submissions: {e}")
            return []
    
    def get_submission(self, test_id: str, student_id: str) -> Optional[Dict]:
        """Get specific submission"""
        try:
            submission = db_manager.execute_query(
                "SELECT * FROM submissions WHERE test_id = ? AND student_id = ?",
                (test_id, student_id),
                fetch_one=True
            )
            
            if submission:
                submission['submission_id'] = submission['submission_id']
                submission['date'] = datetime.fromisoformat(submission['submitted_at'])
                submission['file_id'] = submission['answers']
                submission['graded'] = submission['status'] == 'graded'
                submission['total_score'] = submission.get('score', 0)
                submission['per_question_scores'] = []
                submission['remarks'] = submission.get('feedback', '')
                submission['strengths'] = ''
                submission['improvements'] = ''
                submission['grading_date'] = datetime.fromisoformat(submission['graded_at']) if submission.get('graded_at') else None
            
            return submission
        except Exception as e:
            print(f"Error fetching submission: {e}")
            return None
    
    def get_submission_by_id(self, submission_id: str) -> Optional[Dict]:
        """Get submission by ID"""
        try:
            submission = db_manager.execute_query(
                "SELECT * FROM submissions WHERE submission_id = ?",
                (submission_id,),
                fetch_one=True
            )
            
            if submission:
                submission['submission_id'] = submission['submission_id']
                submission['date'] = datetime.fromisoformat(submission['submitted_at'])
                submission['file_id'] = submission['answers']
                submission['graded'] = submission['status'] == 'graded'
                submission['total_score'] = submission.get('score', 0)
                submission['per_question_scores'] = []
                submission['remarks'] = submission.get('feedback', '')
                submission['strengths'] = ''
                submission['improvements'] = ''
                submission['grading_date'] = datetime.fromisoformat(submission['graded_at']) if submission.get('graded_at') else None
            
            return submission
        except Exception as e:
            print(f"Error fetching submission: {e}")
            return None
    
    def update_submission_scores(self, submission_id: str, total_score: float,
                               per_question_scores: List[Dict], remarks: str = None,
                               strengths: str = None, improvements: str = None,
                               rubric_filled: str = None) -> bool:
        """Update submission with grading results"""
        try:
            db_manager.execute_query(
                """UPDATE submissions 
                   SET score = ?, feedback = ?, status = 'graded', graded_at = CURRENT_TIMESTAMP 
                   WHERE submission_id = ?""",
                (int(total_score), remarks or '', submission_id)
            )
            return True
        except Exception as e:
            print(f"Error updating submission scores: {e}")
            return False
    
    def get_submission_file(self, submission_id: str):
        """Get submission file"""
        try:
            submission = self.get_submission_by_id(submission_id)
            if submission and submission.get('file_id'):
                file_info = db_manager.get_file(submission['file_id'])
                
                # Create a file-like object for compatibility
                class FileObj:
                    def __init__(self, data):
                        self.data = data
                        self.position = 0
                    
                    def read(self, size=-1):
                        if size == -1:
                            result = self.data[self.position:]
                            self.position = len(self.data)
                        else:
                            result = self.data[self.position:self.position + size]
                            self.position += len(result)
                        return result
                
                return FileObj(file_info['data'])
            return None
        except Exception as e:
            print(f"Error fetching submission file: {e}")
            return None
    
    def delete_submission(self, submission_id: str) -> bool:
        """Delete a submission (admin only)"""
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
            
            for submission in submissions:
                submission['submission_id'] = submission['submission_id']
                submission['date'] = datetime.fromisoformat(submission['submitted_at'])
                submission['file_id'] = submission['answers']
                submission['graded'] = submission['status'] == 'graded'
                submission['total_score'] = submission.get('score', 0)
                submission['per_question_scores'] = []
                submission['remarks'] = submission.get('feedback', '')
                submission['strengths'] = ''
                submission['improvements'] = ''
                submission['grading_date'] = datetime.fromisoformat(submission['graded_at']) if submission.get('graded_at') else None
            
            return submissions
        except Exception as e:
            print(f"Error fetching all submissions: {e}")
            return []
    
    def has_student_submitted(self, test_id: str, student_id: str) -> bool:
        """Check if student has already submitted for a test"""
        try:
            result = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM submissions WHERE test_id = ? AND student_id = ?",
                (test_id, student_id),
                fetch_one=True
            )
            return result and result['count'] > 0
        except Exception as e:
            print(f"Error checking submission status: {e}")
            return False

# Global submission manager instance
submission_manager = SubmissionManager()