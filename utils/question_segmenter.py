import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
from typing import List, Dict, Tuple, Optional, Set
import json
from dataclasses import dataclass
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    MATHEMATICAL = "mathematical"
    DIAGRAM = "diagram"
    UNKNOWN = "unknown"

@dataclass
class QuestionBoundary:
    question_number: int
    x: int
    y: int
    width: int
    height: int
    confidence: float
    question_type: QuestionType
    expected_marks: Optional[int] = None
    has_sub_questions: bool = False
    sub_questions: List[int] = None

@dataclass
class AnswerSegment:
    question_number: int
    x: int
    y: int
    width: int
    height: int
    confidence: float
    answer_type: QuestionType
    is_complete: bool = True
    has_working: bool = False
    marks_allocated: Optional[int] = None

@dataclass
class QuestionAnswerMapping:
    question: QuestionBoundary
    answer: Optional[AnswerSegment]
    mapping_confidence: float
    is_missing: bool = False
    validation_errors: List[str] = None

class QuestionSegmenter:
    """Intelligent question segmentation and answer mapping system"""
    
    def __init__(self):
        self.min_question_height = 80
        self.min_question_width = 150
        self.question_number_patterns = [
            r'^(\d+)[\.\)]',  # 1. or 1)
            r'^Q(\d+)',       # Q1
            r'^Question\s*(\d+)',  # Question 1
            r'^(\d+)\s*[a-z]\)',   # 1a), 1b)
        ]
        self.answer_patterns = [
            r'^Answer\s*(\d+)',
            r'^(\d+)[\.\)]\s*Answer',
            r'^Q(\d+)\s*Answer',
        ]
        
    def detect_question_boundaries(self, image_data: bytes) -> List[QuestionBoundary]:
        """Advanced question boundary detection using multiple algorithms"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return []
            
            # Multiple detection methods
            boundaries = []
            
            # Method 1: Contour-based detection
            contour_boundaries = self._detect_by_contours(image)
            boundaries.extend(contour_boundaries)
            
            # Method 2: Text-based detection
            text_boundaries = self._detect_by_text_regions(image)
            boundaries.extend(text_boundaries)
            
            # Method 3: Layout-based detection
            layout_boundaries = self._detect_by_layout_analysis(image)
            boundaries.extend(layout_boundaries)
            
            # Merge and filter boundaries
            merged_boundaries = self._merge_overlapping_boundaries(boundaries)
            filtered_boundaries = self._filter_valid_boundaries(merged_boundaries, image.shape)
            
            # Sort by position and assign question numbers
            sorted_boundaries = self._assign_question_numbers(filtered_boundaries)
            
            return sorted_boundaries
            
        except Exception as e:
            print(f"Error detecting question boundaries: {e}")
            return []
    
    def _detect_by_contours(self, image: np.ndarray) -> List[QuestionBoundary]:
        """Detect question boundaries using contour analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive threshold
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            boundaries = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                # Filter by size and aspect ratio
                if (w >= self.min_question_width and h >= self.min_question_height and
                    area > 1000 and w/h < 5):  # Reasonable aspect ratio
                    
                    confidence = min(area / (w * h), 1.0)
                    boundaries.append(QuestionBoundary(
                        question_number=0,  # Will be assigned later
                        x=x, y=y, width=w, height=h,
                        confidence=confidence,
                        question_type=QuestionType.UNKNOWN
                    ))
            
            return boundaries
            
        except Exception as e:
            print(f"Error in contour detection: {e}")
            return []
    
    def _detect_by_text_regions(self, image: np.ndarray) -> List[QuestionBoundary]:
        """Detect question boundaries by analyzing text regions"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply morphological operations to connect text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated = cv2.dilate(gray, kernel, iterations=2)
            eroded = cv2.erode(dilated, kernel, iterations=1)
            
            # Find text regions
            contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            boundaries = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter text regions that could be questions
                if (w >= 100 and h >= 50 and w/h < 8 and
                    h < image.shape[0] * 0.3):  # Not too tall
                    
                    confidence = 0.7  # Medium confidence for text-based detection
                    boundaries.append(QuestionBoundary(
                        question_number=0,
                        x=x, y=y, width=w, height=h,
                        confidence=confidence,
                        question_type=QuestionType.UNKNOWN
                    ))
            
            return boundaries
            
        except Exception as e:
            print(f"Error in text region detection: {e}")
            return []
    
    def _detect_by_layout_analysis(self, image: np.ndarray) -> List[QuestionBoundary]:
        """Detect question boundaries using layout analysis"""
        try:
            height, width = image.shape[:2]
            
            # Divide image into horizontal strips
            strip_height = height // 10  # 10 strips
            boundaries = []
            
            for i in range(10):
                y_start = i * strip_height
                y_end = min((i + 1) * strip_height, height)
                
                # Analyze each strip
                strip = image[y_start:y_end, 0:width]
                
                # Check if strip contains significant content
                gray_strip = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)
                _, binary_strip = cv2.threshold(gray_strip, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Calculate content density
                content_pixels = np.sum(binary_strip > 0)
                total_pixels = binary_strip.shape[0] * binary_strip.shape[1]
                density = content_pixels / total_pixels
                
                if density > 0.05:  # Significant content threshold
                    boundaries.append(QuestionBoundary(
                        question_number=0,
                        x=0, y=y_start, width=width, height=strip_height,
                        confidence=0.6,
                        question_type=QuestionType.UNKNOWN
                    ))
            
            return boundaries
            
        except Exception as e:
            print(f"Error in layout analysis: {e}")
            return []
    
    def _merge_overlapping_boundaries(self, boundaries: List[QuestionBoundary]) -> List[QuestionBoundary]:
        """Merge overlapping or nearby question boundaries"""
        if not boundaries:
            return []
        
        # Sort by y-coordinate
        sorted_boundaries = sorted(boundaries, key=lambda b: b.y)
        merged = []
        
        for boundary in sorted_boundaries:
            if not merged:
                merged.append(boundary)
                continue
            
            # Check if current boundary overlaps with last merged boundary
            last_boundary = merged[-1]
            
            # Calculate overlap
            overlap_y = max(0, min(last_boundary.y + last_boundary.height, boundary.y + boundary.height) - 
                          max(last_boundary.y, boundary.y))
            overlap_x = max(0, min(last_boundary.x + last_boundary.width, boundary.x + boundary.width) - 
                          max(last_boundary.x, boundary.x))
            
            overlap_area = overlap_y * overlap_x
            last_area = last_boundary.width * last_boundary.height
            current_area = boundary.width * boundary.height
            
            # If significant overlap, merge
            if overlap_area > 0.3 * min(last_area, current_area):
                # Merge boundaries
                merged[-1] = QuestionBoundary(
                    question_number=0,
                    x=min(last_boundary.x, boundary.x),
                    y=min(last_boundary.y, boundary.y),
                    width=max(last_boundary.x + last_boundary.width, boundary.x + boundary.width) - 
                          min(last_boundary.x, boundary.x),
                    height=max(last_boundary.y + last_boundary.height, boundary.y + boundary.height) - 
                           min(last_boundary.y, boundary.y),
                    confidence=max(last_boundary.confidence, boundary.confidence),
                    question_type=QuestionType.UNKNOWN
                )
            else:
                merged.append(boundary)
        
        return merged
    
    def _filter_valid_boundaries(self, boundaries: List[QuestionBoundary], image_shape: Tuple[int, int, int]) -> List[QuestionBoundary]:
        """Filter out invalid question boundaries"""
        height, width = image_shape[:2]
        valid_boundaries = []
        
        for boundary in boundaries:
            # Check size constraints
            if (boundary.width < self.min_question_width or 
                boundary.height < self.min_question_height):
                continue
            
            # Check if boundary is within image bounds
            if (boundary.x < 0 or boundary.y < 0 or 
                boundary.x + boundary.width > width or 
                boundary.y + boundary.height > height):
                continue
            
            # Check aspect ratio
            aspect_ratio = boundary.width / boundary.height
            if aspect_ratio > 10 or aspect_ratio < 0.1:  # Too wide or too tall
                continue
            
            valid_boundaries.append(boundary)
        
        return valid_boundaries
    
    def _assign_question_numbers(self, boundaries: List[QuestionBoundary]) -> List[QuestionBoundary]:
        """Assign sequential question numbers to boundaries"""
        # Sort by y-coordinate (top to bottom)
        sorted_boundaries = sorted(boundaries, key=lambda b: b.y)
        
        for i, boundary in enumerate(sorted_boundaries):
            boundary.question_number = i + 1
            
            # Try to determine question type based on size and position
            if boundary.height > 200:
                boundary.question_type = QuestionType.LONG_ANSWER
            elif boundary.height > 100:
                boundary.question_type = QuestionType.SHORT_ANSWER
            else:
                boundary.question_type = QuestionType.MULTIPLE_CHOICE
        
        return sorted_boundaries
    
    def detect_answer_segments(self, image_data: bytes) -> List[AnswerSegment]:
        """Detect answer segments in the image"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return []
            
            # Use similar detection methods as questions
            answer_boundaries = self._detect_by_contours(image)
            
            # Convert to answer segments
            answer_segments = []
            for boundary in answer_boundaries:
                answer_segments.append(AnswerSegment(
                    question_number=boundary.question_number,
                    x=boundary.x, y=boundary.y,
                    width=boundary.width, height=boundary.height,
                    confidence=boundary.confidence,
                    answer_type=boundary.question_type,
                    is_complete=self._check_answer_completeness(boundary, image),
                    has_working=self._check_for_working(boundary, image)
                ))
            
            return answer_segments
            
        except Exception as e:
            print(f"Error detecting answer segments: {e}")
            return []
    
    def _check_answer_completeness(self, boundary: QuestionBoundary, image: np.ndarray) -> bool:
        """Check if an answer segment appears complete"""
        try:
            # Extract the region
            region = image[boundary.y:boundary.y + boundary.height, 
                          boundary.x:boundary.x + boundary.width]
            
            # Convert to grayscale
            gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Check for significant content
            _, binary = cv2.threshold(gray_region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            content_ratio = np.sum(binary > 0) / (binary.shape[0] * binary.shape[1])
            
            # Consider complete if more than 10% of area has content
            return content_ratio > 0.1
            
        except Exception as e:
            print(f"Error checking answer completeness: {e}")
            return True
    
    def _check_for_working(self, boundary: QuestionBoundary, image: np.ndarray) -> bool:
        """Check if answer contains mathematical working"""
        try:
            # Extract the region
            region = image[boundary.y:boundary.y + boundary.height, 
                          boundary.x:boundary.x + boundary.width]
            
            # Convert to grayscale
            gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Look for mathematical symbols and patterns
            # This is a simplified check - in practice, you'd use OCR to detect math symbols
            _, binary = cv2.threshold(gray_region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Check for horizontal lines (fractions, equals signs)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Check for vertical lines (fractions, division)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # If we find significant lines, likely has mathematical working
            horizontal_ratio = np.sum(horizontal_lines > 0) / (binary.shape[0] * binary.shape[1])
            vertical_ratio = np.sum(vertical_lines > 0) / (binary.shape[0] * binary.shape[1])
            
            return horizontal_ratio > 0.02 or vertical_ratio > 0.02
            
        except Exception as e:
            print(f"Error checking for working: {e}")
            return False
    
    def map_questions_to_answers(self, questions: List[QuestionBoundary], 
                                answers: List[AnswerSegment]) -> List[QuestionAnswerMapping]:
        """Map questions to their corresponding answers"""
        mappings = []
        
        # Create a set of answered question numbers
        answered_questions = {answer.question_number for answer in answers}
        
        for question in questions:
            # Find corresponding answer
            corresponding_answer = None
            for answer in answers:
                if answer.question_number == question.question_number:
                    corresponding_answer = answer
                    break
            
            # Check if answer is missing
            is_missing = question.question_number not in answered_questions
            
            # Calculate mapping confidence
            if corresponding_answer:
                # Calculate spatial relationship confidence
                spatial_confidence = self._calculate_spatial_confidence(question, corresponding_answer)
                mapping_confidence = (question.confidence + corresponding_answer.confidence + spatial_confidence) / 3
            else:
                mapping_confidence = question.confidence * 0.5  # Lower confidence for missing answers
            
            # Validate the mapping
            validation_errors = self._validate_question_answer_mapping(question, corresponding_answer)
            
            mappings.append(QuestionAnswerMapping(
                question=question,
                answer=corresponding_answer,
                mapping_confidence=mapping_confidence,
                is_missing=is_missing,
                validation_errors=validation_errors
            ))
        
        return mappings
    
    def _calculate_spatial_confidence(self, question: QuestionBoundary, answer: AnswerSegment) -> float:
        """Calculate confidence based on spatial relationship between question and answer"""
        try:
            # Check if answer is below question (typical layout)
            if answer.y > question.y:
                vertical_confidence = 0.8
            else:
                vertical_confidence = 0.3
            
            # Check horizontal alignment
            horizontal_overlap = max(0, min(question.x + question.width, answer.x + answer.width) - 
                                   max(question.x, answer.x))
            horizontal_confidence = horizontal_overlap / max(question.width, answer.width)
            
            # Check distance
            distance = abs(answer.y - (question.y + question.height))
            distance_confidence = max(0, 1 - distance / 500)  # Decay with distance
            
            return (vertical_confidence + horizontal_confidence + distance_confidence) / 3
            
        except Exception as e:
            print(f"Error calculating spatial confidence: {e}")
            return 0.5
    
    def _validate_question_answer_mapping(self, question: QuestionBoundary, 
                                        answer: Optional[AnswerSegment]) -> List[str]:
        """Validate the mapping between question and answer"""
        errors = []
        
        if not answer:
            errors.append("No answer found for this question")
            return errors
        
        # Check for reasonable size relationship
        question_area = question.width * question.height
        answer_area = answer.width * answer.height
        
        if answer_area < question_area * 0.1:
            errors.append("Answer area seems too small for the question")
        elif answer_area > question_area * 5:
            errors.append("Answer area seems too large for the question")
        
        # Check for reasonable position relationship
        if answer.y < question.y:
            errors.append("Answer appears above question (unusual layout)")
        
        # Check for overlapping regions (shouldn't happen in typical layouts)
        overlap_x = max(0, min(question.x + question.width, answer.x + answer.width) - 
                       max(question.x, answer.x))
        overlap_y = max(0, min(question.y + question.height, answer.y + answer.height) - 
                       max(question.y, answer.y))
        
        if overlap_x > 0 and overlap_y > 0:
            errors.append("Question and answer regions overlap significantly")
        
        return errors
    
    def detect_missing_answers(self, mappings: List[QuestionAnswerMapping]) -> List[QuestionAnswerMapping]:
        """Identify missing answers and provide analysis"""
        missing_answers = []
        
        for mapping in mappings:
            if mapping.is_missing:
                # Analyze why the answer might be missing
                analysis = self._analyze_missing_answer(mapping.question)
                mapping.validation_errors.extend(analysis)
                missing_answers.append(mapping)
        
        return missing_answers
    
    def _analyze_missing_answer(self, question: QuestionBoundary) -> List[str]:
        """Analyze why an answer might be missing"""
        analysis = []
        
        # Check question type - some types might not need written answers
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            analysis.append("Multiple choice question - may not require written answer")
        
        # Check question size - very small questions might be sub-questions
        if question.width * question.height < 5000:  # Small area
            analysis.append("Small question area - might be a sub-question")
        
        # Check position - questions at the bottom might be incomplete
        # (This would need image height context)
        
        return analysis
    
    def validate_sequence(self, mappings: List[QuestionAnswerMapping]) -> Dict[str, any]:
        """Validate the sequence of questions and answers"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check for gaps in question numbering
        question_numbers = [m.question.question_number for m in mappings]
        expected_numbers = set(range(1, max(question_numbers) + 1))
        missing_numbers = expected_numbers - set(question_numbers)
        
        if missing_numbers:
            validation_result["errors"].append(f"Missing question numbers: {sorted(missing_numbers)}")
            validation_result["is_valid"] = False
        
        # Check for duplicate question numbers
        if len(question_numbers) != len(set(question_numbers)):
            validation_result["errors"].append("Duplicate question numbers detected")
            validation_result["is_valid"] = False
        
        # Check for reasonable spacing between questions
        for i in range(1, len(mappings)):
            prev_question = mappings[i-1].question
            curr_question = mappings[i].question
            
            # Check vertical spacing
            spacing = curr_question.y - (prev_question.y + prev_question.height)
            if spacing < 0:
                validation_result["warnings"].append(f"Questions {prev_question.question_number} and {curr_question.question_number} overlap vertically")
            elif spacing > 200:
                validation_result["suggestions"].append(f"Large gap between questions {prev_question.question_number} and {curr_question.question_number}")
        
        # Check answer completeness
        missing_count = sum(1 for m in mappings if m.is_missing)
        if missing_count > 0:
            validation_result["warnings"].append(f"{missing_count} questions have missing answers")
        
        return validation_result
    
    def generate_segmentation_report(self, mappings: List[QuestionAnswerMapping], 
                                   validation_result: Dict[str, any]) -> str:
        """Generate a comprehensive segmentation report"""
        report = []
        report.append("=== QUESTION SEGMENTATION REPORT ===\n")
        
        # Summary statistics
        total_questions = len(mappings)
        answered_questions = sum(1 for m in mappings if not m.is_missing)
        missing_questions = total_questions - answered_questions
        
        report.append(f"Total Questions Detected: {total_questions}")
        report.append(f"Questions with Answers: {answered_questions}")
        report.append(f"Questions Missing Answers: {missing_questions}")
        report.append(f"Answer Completion Rate: {(answered_questions/total_questions)*100:.1f}%\n")
        
        # Validation status
        if validation_result["is_valid"]:
            report.append("✅ Sequence Validation: PASSED")
        else:
            report.append("❌ Sequence Validation: FAILED")
        
        # Errors
        if validation_result["errors"]:
            report.append("\n❌ ERRORS:")
            for error in validation_result["errors"]:
                report.append(f"  • {error}")
        
        # Warnings
        if validation_result["warnings"]:
            report.append("\n⚠️ WARNINGS:")
            for warning in validation_result["warnings"]:
                report.append(f"  • {warning}")
        
        # Suggestions
        if validation_result["suggestions"]:
            report.append("\n💡 SUGGESTIONS:")
            for suggestion in validation_result["suggestions"]:
                report.append(f"  • {suggestion}")
        
        # Detailed question analysis
        report.append("\n=== DETAILED ANALYSIS ===")
        for mapping in mappings:
            report.append(f"\nQuestion {mapping.question.question_number}:")
            report.append(f"  Type: {mapping.question.question_type.value}")
            report.append(f"  Position: ({mapping.question.x}, {mapping.question.y})")
            report.append(f"  Size: {mapping.question.width} x {mapping.question.height}")
            report.append(f"  Confidence: {mapping.question.confidence:.2f}")
            
            if mapping.answer:
                report.append(f"  Answer: Found (Confidence: {mapping.answer.confidence:.2f})")
                report.append(f"    Complete: {'Yes' if mapping.answer.is_complete else 'No'}")
                report.append(f"    Has Working: {'Yes' if mapping.answer.has_working else 'No'}")
            else:
                report.append("  Answer: MISSING")
            
            if mapping.validation_errors:
                report.append("  Issues:")
                for error in mapping.validation_errors:
                    report.append(f"    • {error}")
        
        return "\n".join(report)

# Global question segmenter instance
question_segmenter = QuestionSegmenter()
