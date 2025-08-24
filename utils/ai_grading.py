import os
import base64
import json
from typing import Dict, List, Optional
from openai import OpenAI
from utils.database import db_manager

class AIGradingManager:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == "your_openai_api_key_here":
            print("⚠️ OpenAI API key not configured. AI grading will be disabled.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"⚠️ OpenAI client initialization failed: {e}")
                self.client = None
        
        self.model = "gpt-4o-mini"
        self.max_retries = 3
    
    def extract_text_from_image(self, image_data: bytes, prompt: Optional[str] = None) -> str:
        """Extract text from image using GPT-4o-mini vision capabilities with advanced preprocessing"""
        try:
            if not prompt:
                prompt = "Extract all text from this image accurately. Preserve formatting and structure."
            
            # Import image processor
            from utils.image_processor import image_processor
            
            # Preprocess image for better OCR
            processed_images = image_processor.preprocess_image(image_data)
            
            all_extracted_text = []
            
            for i, processed_image in enumerate(processed_images):
                # For multi-page documents, add page context
                page_context = f" (Page {i+1})" if len(processed_images) > 1 else ""
                enhanced_prompt = f"{prompt}{page_context}"
                
                import base64
                base64_image = base64.b64encode(processed_image).decode('utf-8')
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": enhanced_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                    max_tokens=2000
                )
                
                extracted_text = response.choices[0].message.content
                all_extracted_text.append(extracted_text)
            
            # Combine text from all pages
            return "\n\n--- Page Break ---\n\n".join(all_extracted_text)
            
        except Exception as e:
            print(f"Error in OCR: {e}")
            return f"Error extracting text: {str(e)}"
    
    def extract_questions_by_region(self, image_data: bytes, custom_prompt: str = None) -> List[Dict]:
        """Extract questions by slicing image into regions and processing each separately"""
        try:
            from utils.image_processor import image_processor
            
            # Slice image into question regions
            sliced_questions = image_processor.slice_image_by_questions(image_data)
            
            extracted_questions = []
            
            for sliced_question in sliced_questions:
                question_number = sliced_question['question_number']
                question_image = sliced_question['image_data']
                confidence = sliced_question['confidence']
                
                # Extract text from this question region
                question_prompt = custom_prompt or f"Extract the text for question {question_number}. Include the question number and all content."
                question_text = self.extract_text_from_image(question_image, question_prompt)
                
                extracted_questions.append({
                    'question_number': question_number,
                    'question_text': question_text,
                    'confidence': confidence,
                    'region': sliced_question['region']
                })
            
            return extracted_questions
            
        except Exception as e:
            print(f"Error extracting questions by region: {e}")
            return []
    
    def extract_answers_by_region(self, image_data: bytes, custom_prompt: str = None) -> List[Dict]:
        """Extract answers by slicing image into regions and processing each separately"""
        try:
            from utils.image_processor import image_processor
            
            # Slice image into answer regions
            sliced_answers = image_processor.slice_image_by_questions(image_data)
            
            extracted_answers = []
            
            for sliced_answer in sliced_answers:
                answer_number = sliced_answer['question_number']
                answer_image = sliced_answer['image_data']
                confidence = sliced_answer['confidence']
                
                # Extract text from this answer region
                answer_prompt = custom_prompt or f"Extract the answer for question {answer_number}. Include all written work, calculations, and final answers."
                answer_text = self.extract_text_from_image(answer_image, answer_prompt)
                
                extracted_answers.append({
                    'question_number': answer_number,
                    'answer_text': answer_text,
                    'confidence': confidence,
                    'region': sliced_answer['region']
                })
            
            return extracted_answers
            
        except Exception as e:
            print(f"Error extracting answers by region: {e}")
            return []
    
    def grade_submission(self, submission_id: str) -> Dict:
        """Grade a submission using AI"""
        try:
            from utils.submission_manager import submission_manager
            from utils.test_manager import test_manager
            
            # Get submission
            submission = submission_manager.get_submission_by_id(submission_id)
            if not submission:
                return {"success": False, "error": "Submission not found"}
            
            # Get test details
            test = test_manager.get_test_by_id(submission['test_id'])
            if not test:
                return {"success": False, "error": "Test not found"}
            
            # Get answer file
            answer_file = submission_manager.get_submission_file(submission_id)
            if not answer_file:
                return {"success": False, "error": "Answer file not found"}
            
            # Extract text from answer (OCR)
            answer_text = self.extract_text_from_image(answer_file.read())
            
            # Grade the answer
            grading_result = self._grade_answer(
                "Questions from test paper", 
                answer_text,
                test.get('rubric'),
                test['subject'],
                test['title']
            )
            
            if grading_result["success"]:
                # Update submission with results
                success = submission_manager.update_submission_scores(
                    submission_id,
                    grading_result["total_score"],
                    grading_result["per_question_scores"],
                    grading_result.get("remarks"),
                    grading_result.get("strengths"),
                    grading_result.get("improvements"),
                    grading_result.get("rubric_filled")
                )
                
                if success:
                    return {"success": True, "message": "Grading completed successfully"}
                else:
                    return {"success": False, "error": "Failed to save grading results"}
            else:
                return grading_result
                
        except Exception as e:
            print(f"Error in grade_submission: {e}")
            return {"success": False, "error": f"Grading failed: {str(e)}"}
    
    def _grade_answer(self, questions: str, answers: str, rubric: str, subject: str, test_title: str) -> Dict:
        """Internal method to grade answers using AI"""
        try:
            # Simple grading prompt
            prompt = f"""Grade this student submission for {subject}.

Test: {test_title}
Questions: {questions}
Student Answers: {answers}
Rubric: {rubric if rubric else "Standard grading criteria"}

Provide:
1. Total Score (0-100)
2. Remarks: General feedback
3. Strengths: What student did well
4. Improvements: Areas to improve

Format as:
Total Score: [number]
Remarks: [text]
Strengths: [text]
Improvements: [text]"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            parsed_result = self._parse_grading_response(result_text)
            
            return {"success": True, **parsed_result}
            
        except Exception as e:
            print(f"Error in _grade_answer: {e}")
            return {"success": False, "error": f"AI grading failed: {str(e)}"}
    
    def _parse_grading_response(self, response_text: str) -> Dict:
        """Parse AI grading response"""
        result = {
            "total_score": 75.0,  # Default score
            "per_question_scores": [],
            "remarks": "",
            "strengths": "",
            "improvements": "",
            "rubric_filled": ""
        }
        
        lines = response_text.strip().split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "total score" in line.lower():
                import re
                score_match = re.search(r'(\d+(?:\.\d+)?)', line)
                if score_match:
                    result["total_score"] = float(score_match.group(1))
            
            elif line.lower().startswith("remarks:"):
                result["remarks"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("strengths:"):
                result["strengths"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("improvements:"):
                result["improvements"] = line.split(":", 1)[1].strip()
        
        return result
    
    def _get_ocr_prompt(self) -> str:
        """Get OCR prompt from database or return default"""
        try:
            settings_collection = db_manager.get_collection('settings')
            setting = settings_collection.find_one({"prompt_type": "ocr"})
            if setting:
                return setting['prompt_text']
        except:
            pass
        
        return "Extract all text from this image accurately. Preserve formatting and structure."
    
    def _get_grading_prompt(self) -> str:
        """Get grading prompt from database or return default"""
        try:
            setting = db_manager.execute_query(
                "SELECT prompt_text FROM settings WHERE prompt_type = ?",
                ("grading",),
                fetch_one=True
            )
            if setting:
                return setting['prompt_text']
        except:
            pass
        
        return "Grade this student submission carefully and provide constructive feedback."
    
    def grade_with_retry(self, submission_id: str) -> Dict:
        """Grade submission with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                result = self.grade_submission(submission_id)
                if result.get("success"):
                    return result
                print(f"Grading attempt {attempt + 1} failed: {result.get('error')}")
            except Exception as e:
                print(f"Grading attempt {attempt + 1} exception: {e}")
            
            if attempt < self.max_retries - 1:
                import time
                time.sleep(2 ** attempt)
        
        return {"success": False, "error": "All grading attempts failed"}
    
    def test_api_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self.client:
            print("❌ OpenAI client not initialized. Check your API key in .env file.")
            return False
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"API connection test failed: {e}")
            return False
    
    def extract_rubric_from_image(self, image_data: bytes, custom_prompt: str = None) -> dict:
        """Extract rubric table from image using GPT-4o-mini vision capabilities"""
        if not self.client:
            return {"success": False, "error": "OpenAI client not initialized"}
        
        try:
            prompt = custom_prompt if custom_prompt else self._get_rubric_extraction_prompt()
            
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            extracted_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                import json
                rubric_data = json.loads(extracted_text)
                return {"success": True, "rubric_data": rubric_data}
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"success": True, "rubric_text": extracted_text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_test_questions_from_image(self, image_data: bytes, custom_prompt: str = None) -> dict:
        """Extract test questions from image using GPT-4o-mini vision capabilities"""
        if not self.client:
            return {"success": False, "error": "OpenAI client not initialized"}
        
        try:
            prompt = custom_prompt if custom_prompt else self._get_test_extraction_prompt()
            
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            extracted_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                import json
                questions_data = json.loads(extracted_text)
                return {"success": True, "questions_data": questions_data}
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"success": True, "questions_text": extracted_text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_rubric_extraction_prompt(self) -> str:
        """Get rubric extraction prompt from database settings"""
        try:
            prompt_data = db_manager.execute_query(
                "SELECT prompt_text FROM settings WHERE prompt_type = ?",
                ("rubric_extraction",),
                fetch_one=True
            )
            return prompt_data["prompt_text"] if prompt_data else "Extract the rubric table from this image in JSON format."
        except Exception as e:
            print(f"Error getting rubric extraction prompt: {e}")
            return "Extract the rubric table from this image in JSON format."
    
    def _get_test_extraction_prompt(self) -> str:
        """Get test extraction prompt from database settings"""
        try:
            prompt_data = db_manager.execute_query(
                "SELECT prompt_text FROM settings WHERE prompt_type = ?",
                ("test_extraction",),
                fetch_one=True
            )
            return prompt_data["prompt_text"] if prompt_data else "Extract all questions from this test paper in JSON format."
        except Exception as e:
            print(f"Error getting test extraction prompt: {e}")
            return "Extract all questions from this test paper in JSON format."
    
    def _get_answer_extraction_prompt(self) -> str:
        """Get answer extraction prompt from database settings"""
        try:
            prompt_data = db_manager.execute_query(
                "SELECT prompt_text FROM settings WHERE prompt_type = ?",
                ("answer_extraction",),
                fetch_one=True
            )
            return prompt_data["prompt_text"] if prompt_data else "Extract student answers from this answer sheet in JSON format."
        except Exception as e:
            print(f"Error getting answer extraction prompt: {e}")
            return "Extract student answers from this answer sheet in JSON format."

# Global AI grading manager instance
ai_grading_manager = AIGradingManager()