import asyncio
import threading
import queue
import time
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import traceback
import hashlib
import os

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class ProcessingPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class ProcessingTask:
    task_id: str
    task_type: str
    data: Dict
    priority: ProcessingPriority
    status: ProcessingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None

@dataclass
class ProcessingMetrics:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_processing_time: float = 0.0
    queue_size: int = 0
    active_workers: int = 0
    uptime: float = 0.0

class ProcessingPipeline:
    """Asynchronous processing pipeline with queue management and error recovery"""
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # Priority queues for different task types
        self.queues = {
            ProcessingPriority.URGENT: queue.PriorityQueue(maxsize=max_queue_size),
            ProcessingPriority.HIGH: queue.PriorityQueue(maxsize=max_queue_size),
            ProcessingPriority.NORMAL: queue.PriorityQueue(maxsize=max_queue_size),
            ProcessingPriority.LOW: queue.PriorityQueue(maxsize=max_queue_size)
        }
        
        # Task tracking
        self.tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: Dict[str, ProcessingTask] = {}
        self.failed_tasks: Dict[str, ProcessingTask] = {}
        
        # Processing state
        self.is_running = False
        self.workers: List[threading.Thread] = []
        self.metrics = ProcessingMetrics()
        self.start_time = datetime.now()
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.retry_delays = [1, 5, 15, 30]  # Seconds between retries
        
        # Task handlers
        self.task_handlers: Dict[str, Callable] = {}
        
        # Setup logging
        self._setup_logging()
        
        # Register default handlers
        self._register_default_handlers()
    
    def _setup_logging(self):
        """Setup logging for the processing pipeline"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('processing_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ProcessingPipeline')
    
    def _register_default_handlers(self):
        """Register default task handlers"""
        self.register_handler('ocr_extraction', self._handle_ocr_extraction)
        self.register_handler('grading', self._handle_grading)
        self.register_handler('report_generation', self._handle_report_generation)
        self.register_handler('file_processing', self._handle_file_processing)
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler for a specific task type"""
        self.task_handlers[task_type] = handler
        self.logger.info(f"Registered handler for task type: {task_type}")
    
    def start(self):
        """Start the processing pipeline"""
        if self.is_running:
            self.logger.warning("Processing pipeline is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Processing pipeline started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the processing pipeline"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.logger.info("Processing pipeline stopped")
    
    def submit_task(self, task_type: str, data: Dict, priority: ProcessingPriority = ProcessingPriority.NORMAL) -> str:
        """Submit a task to the processing pipeline"""
        task_id = self._generate_task_id(task_type, data)
        
        task = ProcessingTask(
            task_id=task_id,
            task_type=task_type,
            data=data,
            priority=priority,
            status=ProcessingStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Add to tracking
        self.tasks[task_id] = task
        self.metrics.total_tasks += 1
        
        # Add to appropriate queue
        try:
            self.queues[priority].put((priority.value, task_id), timeout=1)
            self.metrics.queue_size += 1
            self.logger.info(f"Task {task_id} submitted with priority {priority.name}")
            return task_id
        except queue.Full:
            self.logger.error(f"Queue full, cannot submit task {task_id}")
            task.status = ProcessingStatus.FAILED
            task.error_message = "Queue full"
            self.failed_tasks[task_id] = task
            return task_id
    
    def _generate_task_id(self, task_type: str, data: Dict) -> str:
        """Generate a unique task ID"""
        content = f"{task_type}_{json.dumps(data, sort_keys=True)}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _worker_loop(self, worker_id: int):
        """Main worker loop for processing tasks"""
        self.logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get task from highest priority queue
                task_id = None
                for priority in [ProcessingPriority.URGENT, ProcessingPriority.HIGH, 
                               ProcessingPriority.NORMAL, ProcessingPriority.LOW]:
                    try:
                        _, task_id = self.queues[priority].get(timeout=1)
                        break
                    except queue.Empty:
                        continue
                
                if task_id is None:
                    continue
                
                # Process the task
                self._process_task(task_id, worker_id)
                
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(1)
        
        self.logger.info(f"Worker {worker_id} stopped")
    
    def _process_task(self, task_id: str, worker_id: int):
        """Process a single task"""
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Task {task_id} not found")
            return
        
        try:
            # Update task status
            task.status = ProcessingStatus.PROCESSING
            task.started_at = datetime.now()
            self.metrics.active_workers += 1
            self.metrics.queue_size -= 1
            
            self.logger.info(f"Worker {worker_id} processing task {task_id} ({task.task_type})")
            
            # Get handler for task type
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Process the task
            start_time = time.time()
            result = handler(task.data)
            processing_time = time.time() - start_time
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(task, result)
            
            # Update task with results
            task.status = ProcessingStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.confidence_score = confidence_score
            task.processing_time = processing_time
            
            # Move to completed tasks
            self.completed_tasks[task_id] = task
            del self.tasks[task_id]
            
            # Update metrics
            self.metrics.completed_tasks += 1
            self.metrics.active_workers -= 1
            self._update_average_processing_time(processing_time)
            
            self.logger.info(f"Task {task_id} completed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            self._handle_task_error(task, e, worker_id)
    
    def _handle_task_error(self, task: ProcessingTask, error: Exception, worker_id: int):
        """Handle task processing errors with retry logic"""
        task.retry_count += 1
        task.error_message = str(error)
        
        self.logger.error(f"Worker {worker_id} failed to process task {task.task_id}: {error}")
        
        if task.retry_count <= task.max_retries:
            # Retry the task
            task.status = ProcessingStatus.RETRYING
            delay = self.retry_delays[min(task.retry_count - 1, len(self.retry_delays) - 1)]
            
            self.logger.info(f"Retrying task {task.task_id} in {delay}s (attempt {task.retry_count}/{task.max_retries})")
            
            # Schedule retry
            threading.Timer(delay, self._retry_task, args=[task.task_id]).start()
        else:
            # Task failed permanently
            task.status = ProcessingStatus.FAILED
            self.failed_tasks[task.task_id] = task
            del self.tasks[task.task_id]
            
            self.metrics.failed_tasks += 1
            self.metrics.active_workers -= 1
            self.metrics.queue_size -= 1
            
            self.logger.error(f"Task {task.task_id} failed permanently after {task.max_retries} retries")
    
    def _retry_task(self, task_id: str):
        """Retry a failed task"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        # Reset task for retry
        task.status = ProcessingStatus.PENDING
        task.started_at = None
        task.completed_at = None
        task.error_message = None
        task.result = None
        
        # Re-queue the task
        try:
            self.queues[task.priority].put((task.priority.value, task_id), timeout=1)
            self.metrics.queue_size += 1
        except queue.Full:
            self.logger.error(f"Queue full, cannot retry task {task_id}")
            task.status = ProcessingStatus.FAILED
            self.failed_tasks[task_id] = task
            del self.tasks[task_id]
    
    def _calculate_confidence_score(self, task: ProcessingTask, result: Dict) -> float:
        """Calculate confidence score for task processing"""
        base_confidence = 0.8
        
        # Adjust based on task type
        if task.task_type == 'ocr_extraction':
            # Check OCR quality indicators
            text_length = len(result.get('extracted_text', ''))
            if text_length > 100:
                base_confidence += 0.1
            elif text_length < 10:
                base_confidence -= 0.2
            
            # Check for common OCR errors
            if result.get('ocr_errors'):
                base_confidence -= 0.1
        
        elif task.task_type == 'grading':
            # Check grading confidence
            grading_confidence = result.get('grading_confidence', 0.5)
            base_confidence = grading_confidence
        
        elif task.task_type == 'file_processing':
            # Check file processing success
            if result.get('processing_success', False):
                base_confidence += 0.1
            else:
                base_confidence -= 0.2
        
        # Adjust based on processing time
        if task.processing_time:
            if task.processing_time < 5:  # Fast processing
                base_confidence += 0.05
            elif task.processing_time > 30:  # Slow processing
                base_confidence -= 0.05
        
        # Adjust based on retry count
        if task.retry_count > 0:
            base_confidence -= (task.retry_count * 0.1)
        
        return max(0.0, min(1.0, base_confidence))
    
    def _update_average_processing_time(self, new_time: float):
        """Update average processing time"""
        total_completed = self.metrics.completed_tasks
        if total_completed == 1:
            self.metrics.average_processing_time = new_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_processing_time = (
                alpha * new_time + (1 - alpha) * self.metrics.average_processing_time
            )
    
    def get_task_status(self, task_id: str) -> Optional[ProcessingTask]:
        """Get the status of a specific task"""
        return (self.tasks.get(task_id) or 
                self.completed_tasks.get(task_id) or 
                self.failed_tasks.get(task_id))
    
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        self.metrics.uptime = (datetime.now() - self.start_time).total_seconds()
        self.metrics.queue_size = sum(q.qsize() for q in self.queues.values())
        self.metrics.active_workers = sum(1 for task in self.tasks.values() 
                                        if task.status == ProcessingStatus.PROCESSING)
        return self.metrics
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get current queue status"""
        return {
            priority.name: queue.qsize() 
            for priority, queue in self.queues.items()
        }
    
    def clear_completed_tasks(self, older_than_hours: int = 24):
        """Clear completed tasks older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        completed_to_remove = [
            task_id for task_id, task in self.completed_tasks.items()
            if task.completed_at and task.completed_at < cutoff_time
        ]
        
        for task_id in completed_to_remove:
            del self.completed_tasks[task_id]
        
        self.logger.info(f"Cleared {len(completed_to_remove)} old completed tasks")
    
    # Default task handlers
    def _handle_ocr_extraction(self, data: Dict) -> Dict:
        """Handle OCR extraction tasks"""
        try:
            from utils.ai_grading import ai_grading_manager
            from utils.image_processor import image_processor
            
            image_data = data.get('image_data')
            content_type = data.get('content_type')
            
            # Preprocess image
            processed_images = image_processor.preprocess_image(image_data, content_type)
            
            # Extract text from all processed images
            all_text = []
            ocr_errors = []
            
            for i, processed_image in enumerate(processed_images):
                try:
                    text = ai_grading_manager.extract_text_from_image(processed_image)
                    all_text.append(text)
                except Exception as e:
                    ocr_errors.append(f"Page {i+1}: {str(e)}")
            
            return {
                'extracted_text': '\n'.join(all_text),
                'ocr_errors': ocr_errors,
                'pages_processed': len(processed_images),
                'processing_success': len(ocr_errors) == 0
            }
            
        except Exception as e:
            self.logger.error(f"OCR extraction error: {e}")
            raise
    
    def _handle_grading(self, data: Dict) -> Dict:
        """Handle grading tasks"""
        try:
            from utils.advanced_grading import advanced_grading_system
            
            submission_id = data.get('submission_id')
            test_data = data.get('test_data', {})
            answer_data = data.get('answer_data', {})
            rubric_data = data.get('rubric_data', {})
            
            # Perform advanced grading
            grading_result = advanced_grading_system.grade_submission_advanced(
                submission_id, test_data, answer_data, rubric_data
            )
            
            return {
                'grading_result': asdict(grading_result),
                'grading_confidence': grading_result.grading_confidence,
                'processing_success': True
            }
            
        except Exception as e:
            self.logger.error(f"Grading error: {e}")
            raise
    
    def _handle_report_generation(self, data: Dict) -> Dict:
        """Handle report generation tasks"""
        try:
            from utils.report_generator import report_generator
            
            grading_result = data.get('grading_result')
            student_info = data.get('student_info', {})
            test_info = data.get('test_info', {})
            report_type = data.get('report_type', 'individual')
            
            if report_type == 'individual':
                filename = report_generator.generate_individual_report_docx(
                    grading_result, student_info, test_info
                )
            else:
                filename = report_generator.generate_class_report_docx(
                    grading_result, student_info, test_info
                )
            
            return {
                'report_filename': filename,
                'report_type': report_type,
                'processing_success': True
            }
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            raise
    
    def _handle_file_processing(self, data: Dict) -> Dict:
        """Handle file processing tasks"""
        try:
            file_data = data.get('file_data')
            file_type = data.get('file_type')
            
            # Basic file validation
            if not file_data or len(file_data) == 0:
                raise ValueError("Empty file data")
            
            # Check file size
            file_size = len(file_data)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                raise ValueError("File too large")
            
            # Process based on file type
            if file_type in ['image/jpeg', 'image/png', 'image/jpg']:
                # Image processing
                from utils.image_processor import image_processor
                processed_images = image_processor.preprocess_image(file_data, file_type)
                
                return {
                    'processed_files': len(processed_images),
                    'file_size': file_size,
                    'processing_success': True
                }
            
            elif file_type == 'application/pdf':
                # PDF processing
                from utils.image_processor import image_processor
                processed_images = image_processor.preprocess_image(file_data, file_type)
                
                return {
                    'processed_files': len(processed_images),
                    'file_size': file_size,
                    'processing_success': True
                }
            
            else:
                return {
                    'processed_files': 1,
                    'file_size': file_size,
                    'processing_success': True
                }
                
        except Exception as e:
            self.logger.error(f"File processing error: {e}")
            raise

# Global processing pipeline instance
processing_pipeline = ProcessingPipeline()
