import json
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from datetime import datetime
import math

class GradingCriteria(Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    METHODOLOGY = "methodology"
    PRESENTATION = "presentation"
    MATHEMATICAL_REASONING = "mathematical_reasoning"
    CONCEPTUAL_UNDERSTANDING = "conceptual_understanding"

@dataclass
class StepEvaluation:
    step_number: int
    step_description: str
    is_correct: bool
    partial_credit: float  # 0.0 to 1.0
    feedback: str
    reasoning: str
    confidence: float

@dataclass
class QuestionScore:
    question_number: int
    total_marks: float
    awarded_marks: float
    percentage: float
    step_evaluations: List[StepEvaluation]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    mathematical_reasoning_score: float
    conceptual_understanding_score: float
    presentation_score: float
    overall_feedback: str
    confidence: float

@dataclass
class GradingResult:
    submission_id: str
    student_id: str
    test_id: str
    total_score: float
    max_possible_score: float
    percentage: float
    question_scores: List[QuestionScore]
    overall_feedback: str
    strengths: List[str]
    areas_for_improvement: List[str]
    grading_confidence: float
    grading_time: datetime
    rubric_compliance: Dict[str, float]
    performance_analysis: Dict[str, Any]

class AdvancedGradingSystem:
    """Advanced AI grading system with granular assessment capabilities"""
    
    def __init__(self):
        self.grading_criteria = {
            GradingCriteria.ACCURACY: 0.4,
            GradingCriteria.COMPLETENESS: 0.2,
            GradingCriteria.METHODOLOGY: 0.15,
            GradingCriteria.PRESENTATION: 0.1,
            GradingCriteria.MATHEMATICAL_REASONING: 0.1,
            GradingCriteria.CONCEPTUAL_UNDERSTANDING: 0.05
        }
        
    def grade_submission_advanced(self, submission_id: str, test_data: Dict, 
                                answer_data: Dict, rubric_data: Dict) -> GradingResult:
        """Advanced grading with step-by-step evaluation and partial credit"""
        try:
            from utils.submission_manager import submission_manager
            from utils.test_manager import test_manager
            from utils.ai_grading import ai_grading_manager
            
            # Get submission details
            submission = submission_manager.get_submission_by_id(submission_id)
            if not submission:
                raise ValueError("Submission not found")
            
            # Extract questions and answers
            questions = self._extract_questions(test_data)
            answers = self._extract_answers(answer_data)
            
            # Grade each question individually
            question_scores = []
            total_awarded = 0
            total_possible = 0
            
            for question in questions:
                answer = self._find_corresponding_answer(question['number'], answers)
                question_score = self._grade_individual_question(
                    question, answer, rubric_data, ai_grading_manager
                )
                question_scores.append(question_score)
                total_awarded += question_score.awarded_marks
                total_possible += question_score.total_marks
            
            # Calculate overall scores
            percentage = (total_awarded / total_possible * 100) if total_possible > 0 else 0
            
            # Generate overall feedback
            overall_feedback = self._generate_overall_feedback(question_scores, percentage)
            
            # Identify strengths and weaknesses
            strengths = self._identify_strengths(question_scores)
            areas_for_improvement = self._identify_weaknesses(question_scores)
            
            # Calculate grading confidence
            grading_confidence = self._calculate_grading_confidence(question_scores)
            
            # Analyze rubric compliance
            rubric_compliance = self._analyze_rubric_compliance(question_scores, rubric_data)
            
            # Performance analysis
            performance_analysis = self._analyze_performance(question_scores, submission)
            
            return GradingResult(
                submission_id=submission_id,
                student_id=submission['student_id'],
                test_id=submission['test_id'],
                total_score=total_awarded,
                max_possible_score=total_possible,
                percentage=percentage,
                question_scores=question_scores,
                overall_feedback=overall_feedback,
                strengths=strengths,
                areas_for_improvement=areas_for_improvement,
                grading_confidence=grading_confidence,
                grading_time=datetime.now(),
                rubric_compliance=rubric_compliance,
                performance_analysis=performance_analysis
            )
            
        except Exception as e:
            print(f"Error in advanced grading: {e}")
            raise
    
    def _extract_questions(self, test_data: Dict) -> List[Dict]:
        """Extract questions from test data"""
        questions = []
        
        if isinstance(test_data, dict) and 'questions' in test_data:
            for q in test_data['questions']:
                questions.append({
                    'number': q.get('question_no', 0),
                    'text': q.get('question_text', ''),
                    'marks': q.get('marks', 0),
                    'type': q.get('type', 'unknown')
                })
        elif isinstance(test_data, str):
            # Parse questions from text
            lines = test_data.split('\n')
            current_question = None
            
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+[\.\)]', line):
                    if current_question:
                        questions.append(current_question)
                    current_question = {
                        'number': len(questions) + 1,
                        'text': line,
                        'marks': 10,  # Default marks
                        'type': 'unknown'
                    }
                elif current_question:
                    current_question['text'] += ' ' + line
            
            if current_question:
                questions.append(current_question)
        
        return questions
    
    def _extract_answers(self, answer_data: Dict) -> List[Dict]:
        """Extract answers from answer data"""
        answers = []
        
        if isinstance(answer_data, dict) and 'answers' in answer_data:
            for a in answer_data['answers']:
                answers.append({
                    'number': a.get('question_no', 0),
                    'text': a.get('answer_text', ''),
                    'working_shown': a.get('working_shown', False)
                })
        elif isinstance(answer_data, str):
            # Parse answers from text
            lines = answer_data.split('\n')
            current_answer = None
            
            for line in lines:
                line = line.strip()
                if re.match(r'^Answer\s*\d+', line) or re.match(r'^\d+[\.\)]', line):
                    if current_answer:
                        answers.append(current_answer)
                    current_answer = {
                        'number': len(answers) + 1,
                        'text': line,
                        'working_shown': False
                    }
                elif current_answer:
                    current_answer['text'] += ' ' + line
            
            if current_answer:
                answers.append(current_answer)
        
        return answers
    
    def _find_corresponding_answer(self, question_number: int, answers: List[Dict]) -> Optional[Dict]:
        """Find the answer corresponding to a question"""
        for answer in answers:
            if answer['number'] == question_number:
                return answer
        return None
    
    def _grade_individual_question(self, question: Dict, answer: Optional[Dict], 
                                 rubric_data: Dict, ai_grading_manager) -> QuestionScore:
        """Grade an individual question with step-by-step evaluation"""
        try:
            question_number = question['number']
            max_marks = float(question.get('marks', 10))
            
            if not answer:
                # No answer provided
                return QuestionScore(
                    question_number=question_number,
                    total_marks=max_marks,
                    awarded_marks=0.0,
                    percentage=0.0,
                    step_evaluations=[],
                    strengths=[],
                    weaknesses=["No answer provided"],
                    suggestions=["Ensure all questions are attempted"],
                    mathematical_reasoning_score=0.0,
                    conceptual_understanding_score=0.0,
                    presentation_score=0.0,
                    overall_feedback="No answer provided for this question",
                    confidence=1.0
                )
            
            # Analyze the answer using AI
            analysis_prompt = self._create_analysis_prompt(question, answer, rubric_data)
            analysis_result = ai_grading_manager._grade_answer_advanced(
                question['text'], answer['text'], rubric_data, analysis_prompt
            )
            
            # Extract step-by-step evaluation
            step_evaluations = self._extract_step_evaluations(analysis_result)
            
            # Calculate partial credit
            awarded_marks = self._calculate_partial_credit(step_evaluations, max_marks)
            percentage = (awarded_marks / max_marks * 100) if max_marks > 0 else 0
            
            # Extract strengths and weaknesses
            strengths = analysis_result.get('strengths', [])
            weaknesses = analysis_result.get('weaknesses', [])
            suggestions = analysis_result.get('suggestions', [])
            
            # Calculate component scores
            mathematical_reasoning = self._calculate_mathematical_reasoning_score(step_evaluations)
            conceptual_understanding = self._calculate_conceptual_understanding_score(analysis_result)
            presentation = self._calculate_presentation_score(answer)
            
            # Calculate confidence
            confidence = self._calculate_question_confidence(step_evaluations, analysis_result)
            
            return QuestionScore(
                question_number=question_number,
                total_marks=max_marks,
                awarded_marks=awarded_marks,
                percentage=percentage,
                step_evaluations=step_evaluations,
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=suggestions,
                mathematical_reasoning_score=mathematical_reasoning,
                conceptual_understanding_score=conceptual_understanding,
                presentation_score=presentation,
                overall_feedback=analysis_result.get('feedback', ''),
                confidence=confidence
            )
            
        except Exception as e:
            print(f"Error grading question {question_number}: {e}")
            # Return default score on error
            return QuestionScore(
                question_number=question_number,
                total_marks=float(question.get('marks', 10)),
                awarded_marks=0.0,
                percentage=0.0,
                step_evaluations=[],
                strengths=[],
                weaknesses=["Error in grading"],
                suggestions=["Please review manually"],
                mathematical_reasoning_score=0.0,
                conceptual_understanding_score=0.0,
                presentation_score=0.0,
                overall_feedback="Error occurred during grading",
                confidence=0.0
            )
    
    def _create_analysis_prompt(self, question: Dict, answer: Dict, rubric_data: Dict) -> str:
        """Create a detailed analysis prompt for AI grading"""
        prompt = f"""
        Analyze this student's answer step-by-step:
        
        Question: {question['text']}
        Student Answer: {answer['text']}
        
        Rubric Criteria: {json.dumps(rubric_data, indent=2)}
        
        Please provide:
        1. Step-by-step evaluation of the solution
        2. Partial credit for each step (0.0 to 1.0)
        3. Mathematical reasoning assessment
        4. Conceptual understanding evaluation
        5. Presentation quality
        6. Overall strengths and weaknesses
        7. Specific suggestions for improvement
        
        Format your response as JSON with the following structure:
        {{
            "steps": [
                {{
                    "step_number": 1,
                    "description": "Step description",
                    "is_correct": true/false,
                    "partial_credit": 0.8,
                    "feedback": "Step-specific feedback",
                    "reasoning": "Why this step is correct/incorrect"
                }}
            ],
            "strengths": ["List of strengths"],
            "weaknesses": ["List of weaknesses"],
            "suggestions": ["List of suggestions"],
            "feedback": "Overall feedback",
            "mathematical_reasoning": 0.8,
            "conceptual_understanding": 0.7,
            "presentation": 0.6
        }}
        """
        return prompt
    
    def _extract_step_evaluations(self, analysis_result: Dict) -> List[StepEvaluation]:
        """Extract step evaluations from AI analysis"""
        step_evaluations = []
        
        if 'steps' in analysis_result:
            for step_data in analysis_result['steps']:
                step_eval = StepEvaluation(
                    step_number=step_data.get('step_number', 0),
                    step_description=step_data.get('description', ''),
                    is_correct=step_data.get('is_correct', False),
                    partial_credit=step_data.get('partial_credit', 0.0),
                    feedback=step_data.get('feedback', ''),
                    reasoning=step_data.get('reasoning', ''),
                    confidence=step_data.get('confidence', 0.8)
                )
                step_evaluations.append(step_eval)
        
        return step_evaluations
    
    def _calculate_partial_credit(self, step_evaluations: List[StepEvaluation], max_marks: float) -> float:
        """Calculate partial credit based on step evaluations"""
        if not step_evaluations:
            return 0.0
        
        total_credit = sum(step.partial_credit for step in step_evaluations)
        average_credit = total_credit / len(step_evaluations)
        
        # Apply weighting based on number of steps
        if len(step_evaluations) > 1:
            # More steps = more complex question, higher weighting for partial credit
            weighted_credit = average_credit * 1.2
        else:
            weighted_credit = average_credit
        
        return min(weighted_credit * max_marks, max_marks)
    
    def _calculate_mathematical_reasoning_score(self, step_evaluations: List[StepEvaluation]) -> float:
        """Calculate mathematical reasoning score"""
        if not step_evaluations:
            return 0.0
        
        # Weight later steps more heavily (more complex reasoning)
        weighted_scores = []
        for i, step in enumerate(step_evaluations):
            weight = 1.0 + (i * 0.2)  # Increase weight for later steps
            weighted_scores.append(step.partial_credit * weight)
        
        return sum(weighted_scores) / len(weighted_scores)
    
    def _calculate_conceptual_understanding_score(self, analysis_result: Dict) -> float:
        """Calculate conceptual understanding score"""
        return analysis_result.get('conceptual_understanding', 0.0)
    
    def _calculate_presentation_score(self, answer: Dict) -> float:
        """Calculate presentation score based on answer structure"""
        text = answer.get('text', '')
        
        # Simple heuristics for presentation quality
        score = 0.5  # Base score
        
        # Check for clear structure
        if re.search(r'\d+[\.\)]', text):  # Numbered steps
            score += 0.2
        
        # Check for mathematical notation
        if re.search(r'[=+\-*/()]', text):  # Mathematical symbols
            score += 0.1
        
        # Check for explanations
        if len(text.split()) > 20:  # Substantial answer
            score += 0.1
        
        # Check for working shown
        if answer.get('working_shown', False):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_question_confidence(self, step_evaluations: List[StepEvaluation], 
                                     analysis_result: Dict) -> float:
        """Calculate confidence in the grading result"""
        if not step_evaluations:
            return 0.0
        
        # Average confidence from step evaluations
        step_confidence = statistics.mean(step.confidence for step in step_evaluations)
        
        # Factor in the clarity of the analysis
        analysis_quality = 0.8  # Base quality
        
        if len(step_evaluations) > 1:
            analysis_quality += 0.1  # More detailed analysis
        
        if analysis_result.get('feedback'):
            analysis_quality += 0.1  # Has feedback
        
        return (step_confidence + analysis_quality) / 2
    
    def _generate_overall_feedback(self, question_scores: List[QuestionScore], percentage: float) -> str:
        """Generate overall feedback based on question scores"""
        if percentage >= 90:
            return "Excellent performance! You have demonstrated a strong understanding of the concepts."
        elif percentage >= 80:
            return "Very good work! You have shown solid understanding with room for minor improvements."
        elif percentage >= 70:
            return "Good effort! You have grasped the main concepts but need to work on details."
        elif percentage >= 60:
            return "Satisfactory work. Focus on improving your problem-solving approach."
        elif percentage >= 50:
            return "You need to review the material more thoroughly and practice problem-solving."
        else:
            return "Significant improvement needed. Consider seeking additional help and practice."
    
    def _identify_strengths(self, question_scores: List[QuestionScore]) -> List[str]:
        """Identify overall strengths from question scores"""
        strengths = []
        
        # Analyze high-scoring questions
        high_scoring = [qs for qs in question_scores if qs.percentage >= 80]
        if high_scoring:
            strengths.append(f"Strong performance on {len(high_scoring)} questions")
        
        # Check for mathematical reasoning
        math_scores = [qs.mathematical_reasoning_score for qs in question_scores]
        if math_scores and statistics.mean(math_scores) >= 0.7:
            strengths.append("Good mathematical reasoning skills")
        
        # Check for conceptual understanding
        concept_scores = [qs.conceptual_understanding_score for qs in question_scores]
        if concept_scores and statistics.mean(concept_scores) >= 0.7:
            strengths.append("Solid conceptual understanding")
        
        return strengths
    
    def _identify_weaknesses(self, question_scores: List[QuestionScore]) -> List[str]:
        """Identify areas for improvement from question scores"""
        weaknesses = []
        
        # Analyze low-scoring questions
        low_scoring = [qs for qs in question_scores if qs.percentage < 60]
        if low_scoring:
            weaknesses.append(f"Need improvement on {len(low_scoring)} questions")
        
        # Check for mathematical reasoning issues
        math_scores = [qs.mathematical_reasoning_score for qs in question_scores]
        if math_scores and statistics.mean(math_scores) < 0.5:
            weaknesses.append("Mathematical reasoning needs improvement")
        
        # Check for presentation issues
        presentation_scores = [qs.presentation_score for qs in question_scores]
        if presentation_scores and statistics.mean(presentation_scores) < 0.5:
            weaknesses.append("Work on presenting solutions more clearly")
        
        return weaknesses
    
    def _calculate_grading_confidence(self, question_scores: List[QuestionScore]) -> float:
        """Calculate overall grading confidence"""
        if not question_scores:
            return 0.0
        
        confidences = [qs.confidence for qs in question_scores]
        return statistics.mean(confidences)
    
    def _analyze_rubric_compliance(self, question_scores: List[QuestionScore], 
                                 rubric_data: Dict) -> Dict[str, float]:
        """Analyze compliance with rubric criteria"""
        compliance = {}
        
        for criteria in GradingCriteria:
            if criteria == GradingCriteria.ACCURACY:
                scores = [qs.percentage / 100 for qs in question_scores]
                compliance[criteria.value] = statistics.mean(scores) if scores else 0.0
            elif criteria == GradingCriteria.MATHEMATICAL_REASONING:
                scores = [qs.mathematical_reasoning_score for qs in question_scores]
                compliance[criteria.value] = statistics.mean(scores) if scores else 0.0
            elif criteria == GradingCriteria.CONCEPTUAL_UNDERSTANDING:
                scores = [qs.conceptual_understanding_score for qs in question_scores]
                compliance[criteria.value] = statistics.mean(scores) if scores else 0.0
            elif criteria == GradingCriteria.PRESENTATION:
                scores = [qs.presentation_score for qs in question_scores]
                compliance[criteria.value] = statistics.mean(scores) if scores else 0.0
            else:
                compliance[criteria.value] = 0.7  # Default score
        
        return compliance
    
    def _analyze_performance(self, question_scores: List[QuestionScore], 
                           submission: Dict) -> Dict[str, Any]:
        """Analyze performance for class-wide comparison"""
        analysis = {
            'question_difficulty': {},
            'time_analysis': {},
            'improvement_areas': [],
            'comparative_metrics': {}
        }
        
        # Analyze question difficulty
        for qs in question_scores:
            difficulty = 'easy' if qs.percentage >= 80 else 'medium' if qs.percentage >= 60 else 'hard'
            analysis['question_difficulty'][qs.question_number] = {
                'difficulty': difficulty,
                'score': qs.percentage,
                'awarded_marks': qs.awarded_marks,
                'total_marks': qs.total_marks
            }
        
        # Identify improvement areas
        low_scoring_questions = [qs for qs in question_scores if qs.percentage < 60]
        for qs in low_scoring_questions:
            analysis['improvement_areas'].append({
                'question_number': qs.question_number,
                'current_score': qs.percentage,
                'target_score': 80,
                'focus_areas': qs.weaknesses
            })
        
        return analysis

# Global advanced grading system instance
advanced_grading_system = AdvancedGradingSystem()
