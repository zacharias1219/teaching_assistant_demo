import uuid
from datetime import datetime
from typing import List, Dict, Optional
from utils.database import db_manager

class TestManager:
    def __init__(self):
        pass
    
    def create_test(self, title: str, subject: str, date: datetime, 
                   rubric: Optional[str] = None, file_data: Optional[bytes] = None, 
                   filename: Optional[str] = None, content_type: Optional[str] = None) -> Optional[str]:
        """Create a new test and return test_id"""
        try:
            # Convert datetime to string for SQLite
            date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)
            
            # Check for duplicate test (same title and date)
            existing = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM tests WHERE title = ? AND date = ?",
                (title.strip(), date_str),
                fetch_one=True
            )
            
            if existing and existing['count'] > 0:
                return None  # Duplicate test
            
            test_id = str(uuid.uuid4())
            file_id = None
            
            # Store file if provided
            if file_data and filename:
                file_id = db_manager.store_file(file_data, filename, content_type)
            
            # Create test record
            db_manager.execute_query(
                """INSERT INTO tests (test_id, title, description, date, questions, total_marks) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (test_id, title.strip(), rubric or "", date_str, file_id or "", 100)
            )
            
            return test_id
            
        except Exception as e:
            print(f"Error creating test: {e}")
            return None
    
    def get_all_tests(self) -> List[Dict]:
        """Get all tests sorted by date (newest first)"""
        try:
            tests = db_manager.execute_query(
                "SELECT * FROM tests ORDER BY date DESC",
                fetch_all=True
            )
            
            # Convert date strings back to datetime objects for compatibility
            for test in tests:
                test['subject'] = test.get('description', 'General')
                test['rubric'] = test.get('description', '')
                test['file_id'] = test.get('questions', '')
                try:
                    test['date'] = datetime.strptime(test['date'], '%Y-%m-%d')
                except:
                    test['date'] = datetime.now()
            
            return tests
        except Exception as e:
            print(f"Error fetching tests: {e}")
            return []
    
    def get_test_by_id(self, test_id: str) -> Optional[Dict]:
        """Get test by ID"""
        try:
            test = db_manager.execute_query(
                "SELECT * FROM tests WHERE test_id = ?",
                (test_id,),
                fetch_one=True
            )
            
            if test:
                test['subject'] = test.get('description', 'General')
                test['rubric'] = test.get('description', '')
                test['file_id'] = test.get('questions', '')
                try:
                    test['date'] = datetime.strptime(test['date'], '%Y-%m-%d')
                except:
                    test['date'] = datetime.now()
            
            return test
        except Exception as e:
            print(f"Error fetching test: {e}")
            return None
    
    def update_test(self, test_id: str, title: str, subject: str, date: datetime,
                   rubric: Optional[str] = None, file_data: Optional[bytes] = None,
                   filename: Optional[str] = None, content_type: Optional[str] = None) -> bool:
        """Update test information"""
        try:
            date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else str(date)
            
            update_data = {
                'title': title.strip(),
                'description': rubric or '',
                'date': date_str
            }
            
            # Handle file update
            if file_data and filename:
                file_id = db_manager.store_file(file_data, filename, content_type)
                update_data['questions'] = file_id
            
            db_manager.execute_query(
                "UPDATE tests SET title = ?, description = ?, date = ? WHERE test_id = ?",
                (update_data['title'], update_data['description'], update_data['date'], test_id)
            )
            
            return True
        except Exception as e:
            print(f"Error updating test: {e}")
            return False
    
    def delete_test(self, test_id: str) -> bool:
        """Delete a test"""
        try:
            # Check if test has any submissions
            submissions = db_manager.execute_query(
                "SELECT COUNT(*) as count FROM submissions WHERE test_id = ?",
                (test_id,),
                fetch_one=True
            )
            
            if submissions and submissions['count'] > 0:
                return False  # Cannot delete test with submissions
            
            db_manager.execute_query(
                "DELETE FROM tests WHERE test_id = ?",
                (test_id,)
            )
            return True
        except Exception as e:
            print(f"Error deleting test: {e}")
            return False
    
    def search_tests(self, query: str) -> List[Dict]:
        """Search tests by title or subject"""
        try:
            tests = db_manager.execute_query(
                "SELECT * FROM tests WHERE title LIKE ? OR description LIKE ? ORDER BY date DESC",
                (f"%{query}%", f"%{query}%"),
                fetch_all=True
            )
            
            for test in tests:
                test['subject'] = test.get('description', 'General')
                test['rubric'] = test.get('description', '')
                test['file_id'] = test.get('questions', '')
                try:
                    test['date'] = datetime.strptime(test['date'], '%Y-%m-%d')
                except:
                    test['date'] = datetime.now()
            
            return tests
        except Exception as e:
            print(f"Error searching tests: {e}")
            return []
    
    def get_tests_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get tests within date range"""
        try:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            tests = db_manager.execute_query(
                "SELECT * FROM tests WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                (start_str, end_str),
                fetch_all=True
            )
            
            for test in tests:
                test['subject'] = test.get('description', 'General')
                test['rubric'] = test.get('description', '')
                test['file_id'] = test.get('questions', '')
                try:
                    test['date'] = datetime.strptime(test['date'], '%Y-%m-%d')
                except:
                    test['date'] = datetime.now()
            
            return tests
        except Exception as e:
            print(f"Error fetching tests by date range: {e}")
            return []
    
    def get_subjects(self) -> List[str]:
        """Get list of all unique subjects"""
        return ["Mathematics", "Science", "English", "History", "Geography"]
    
    def get_test_file(self, test_id: str):
        """Get test file"""
        try:
            test = self.get_test_by_id(test_id)
            if test and test.get('file_id'):
                file_info = db_manager.get_file(test['file_id'])
                
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
            print(f"Error fetching test file: {e}")
            return None
    
    def upload_rubric(self, test_id: str, file_data: bytes, filename: str, content_type: str = None) -> bool:
        """Upload rubric file for a test"""
        try:
            # Store the rubric file
            rubric_file_id = db_manager.store_file(file_data, filename, content_type)
            
            # Update test with rubric file ID
            db_manager.execute_query(
                "UPDATE tests SET rubric_file_id = ? WHERE test_id = ?",
                (rubric_file_id, test_id)
            )
            
            return True
        except Exception as e:
            print(f"Error uploading rubric: {e}")
            return False
    
    def extract_rubric(self, test_id: str, custom_prompt: str = None) -> dict:
        """Extract rubric data from uploaded file using AI with advanced preprocessing"""
        try:
            from utils.ai_grading import ai_grading_manager
            from utils.image_processor import image_processor
            
            # Get test and rubric file
            test = self.get_test_by_id(test_id)
            if not test or not test.get('rubric_file_id'):
                return {"success": False, "error": "No rubric file found for this test"}
            
            # Get file data
            file_info = db_manager.get_file(test['rubric_file_id'])
            if not file_info:
                return {"success": False, "error": "Rubric file not found"}
            
            # Preprocess image for better extraction
            processed_images = image_processor.preprocess_image(
                file_info['data'], 
                file_info.get('content_type')
            )
            
            all_rubric_data = []
            
            for i, processed_image in enumerate(processed_images):
                # Extract rubric from processed image
                result = ai_grading_manager.extract_rubric_from_image(
                    processed_image, 
                    custom_prompt
                )
                
                if result.get('success'):
                    rubric_data = result.get('rubric_data', result.get('rubric_text', ''))
                    all_rubric_data.append(rubric_data)
                else:
                    print(f"Failed to extract rubric from page {i+1}: {result.get('error')}")
            
            if all_rubric_data:
                # Combine rubric data from all pages
                combined_rubric = all_rubric_data[0] if len(all_rubric_data) == 1 else all_rubric_data
                
                # Store extracted rubric data
                import json
                rubric_json = json.dumps(combined_rubric) if isinstance(combined_rubric, dict) else str(combined_rubric)
                
                db_manager.execute_query(
                    "UPDATE tests SET rubric_data = ?, rubric_extracted = 1 WHERE test_id = ?",
                    (rubric_json, test_id)
                )
                
                return {"success": True, "rubric_data": combined_rubric}
            else:
                return {"success": False, "error": "Failed to extract rubric from any page"}
                
        except Exception as e:
            print(f"Error extracting rubric: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_questions_from_test(self, test_id: str, custom_prompt: str = None) -> dict:
        """Extract questions from test paper using advanced OCR"""
        try:
            from utils.ai_grading import ai_grading_manager
            from utils.image_processor import image_processor
            
            # Get test and file
            test = self.get_test_by_id(test_id)
            if not test or not test.get('file_id'):
                return {"success": False, "error": "No test file found"}
            
            # Get file data
            file_info = db_manager.get_file(test['file_id'])
            if not file_info:
                return {"success": False, "error": "Test file not found"}
            
            # Preprocess image
            processed_images = image_processor.preprocess_image(
                file_info['data'], 
                file_info.get('content_type')
            )
            
            all_questions = []
            
            for i, processed_image in enumerate(processed_images):
                # Extract questions by region for better accuracy
                questions_result = ai_grading_manager.extract_questions_by_region(
                    processed_image, 
                    custom_prompt
                )
                
                if questions_result:
                    all_questions.extend(questions_result)
                else:
                    # Fallback to full image extraction
                    questions_text = ai_grading_manager.extract_text_from_image(
                        processed_image, 
                        custom_prompt or "Extract all questions from this test paper"
                    )
                    all_questions.append({
                        'question_number': i + 1,
                        'question_text': questions_text,
                        'confidence': 0.5,
                        'region': {'x': 0, 'y': 0, 'width': 100, 'height': 100}
                    })
            
            if all_questions:
                # Store extracted questions
                import json
                questions_json = json.dumps(all_questions)
                
                db_manager.execute_query(
                    "UPDATE tests SET questions = ? WHERE test_id = ?",
                    (questions_json, test_id)
                )
                
                return {"success": True, "questions": all_questions}
            else:
                return {"success": False, "error": "Failed to extract questions"}
                
        except Exception as e:
            print(f"Error extracting questions: {e}")
            return {"success": False, "error": str(e)}
    
    def get_rubric_data(self, test_id: str) -> dict:
        """Get parsed rubric data for a test"""
        try:
            test = self.get_test_by_id(test_id)
            if not test:
                return {"success": False, "error": "Test not found"}
            
            if not test.get('rubric_data'):
                return {"success": False, "error": "No rubric data available"}
            
            import json
            try:
                rubric_data = json.loads(test['rubric_data'])
                return {"success": True, "rubric_data": rubric_data}
            except json.JSONDecodeError:
                return {"success": True, "rubric_text": test['rubric_data']}
                
        except Exception as e:
            print(f"Error getting rubric data: {e}")
            return {"success": False, "error": str(e)}
    
    def get_rubric_file(self, test_id: str):
        """Get rubric file for display"""
        try:
            test = self.get_test_by_id(test_id)
            if test and test.get('rubric_file_id'):
                file_info = db_manager.get_file(test['rubric_file_id'])
                
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
        except Exception as e:
            print(f"Error getting rubric file: {e}")
            return None

# Global test manager instance
test_manager = TestManager()