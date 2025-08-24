import os
import hashlib
import mimetypes
import tempfile
import shutil
import zipfile
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, BinaryIO
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import magic
import cv2
import numpy as np
from PIL import Image, ImageOps
import fitz  # PyMuPDF
import io
import base64

@dataclass
class FileValidationResult:
    is_valid: bool
    file_type: str
    file_size: int
    mime_type: str
    hash_sha256: str
    virus_scan_result: Optional[str] = None
    validation_errors: List[str] = None
    warnings: List[str] = None

@dataclass
class FileProcessingResult:
    original_file: str
    processed_files: List[str]
    compression_ratio: float
    processing_time: float
    file_metadata: Dict[str, Any]
    validation_result: FileValidationResult
    temporary_files: List[str] = None

class EnhancedFileProcessor:
    """Enhanced file processing with validation, virus scanning, compression, and multi-page support"""
    
    def __init__(self, temp_dir: str = None, max_file_size: int = 100 * 1024 * 1024):  # 100MB
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="file_processor_")
        self.max_file_size = max_file_size
        self.supported_formats = {
            'image': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'],
            'document': ['pdf', 'doc', 'docx', 'txt'],
            'archive': ['zip', 'rar', '7z']
        }
        
        # Setup logging
        self.logger = logging.getLogger('EnhancedFileProcessor')
        
        # Virus signature patterns (basic implementation)
        self.virus_signatures = [
            b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
            b'TVqQAAMAAAAEAAAA//8AALgAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAA4fug4AtAnNIbgBTM0hVGhpcyBwcm9ncmFtIGNhbm5vdCBiZSBydW4gaW4gRE9TIG1vZGUuDQ0KJAAAAAAAAABQRQAATAEDAFKmq1UAAAAAAAAAAOAAIiALATAAAA4AAAAGAAAAAAAAvjoAAAAgAAAAQAAAAAAAEAAgAAAAAgAABAAAAAAAAAAGAAAAAAAAAACAAAAAAgAAAAAAAAMAYIUAABAAABAAAAAAEAAAEAAAAAAAABAAAAAAAAAAAAAAAGQ6AABPAAAAAEAAAIgDAAAAAAAAAAAAAAAAAAAAAAAAAGAAAAwAAADcOAAAOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='
        ]
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def process_file(self, file_path: str, file_data: bytes = None, 
                    enable_compression: bool = True, enable_virus_scan: bool = True) -> FileProcessingResult:
        """Process a file with full validation and enhancement"""
        start_time = datetime.now()
        
        try:
            # Read file data if not provided
            if file_data is None:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
            
            # Validate file
            validation_result = self._validate_file(file_path, file_data, enable_virus_scan)
            
            if not validation_result.is_valid:
                raise ValueError(f"File validation failed: {validation_result.validation_errors}")
            
            # Process based on file type
            processed_files = []
            compression_ratio = 1.0
            
            if validation_result.file_type == 'image':
                processed_files = self._process_image_file(file_data, enable_compression)
                if enable_compression and len(processed_files) > 1:
                    compression_ratio = len(file_data) / sum(os.path.getsize(f) for f in processed_files)
            
            elif validation_result.file_type == 'document':
                processed_files = self._process_document_file(file_data, enable_compression)
                if enable_compression and len(processed_files) > 1:
                    compression_ratio = len(file_data) / sum(os.path.getsize(f) for f in processed_files)
            
            elif validation_result.file_type == 'archive':
                processed_files = self._process_archive_file(file_data)
            
            else:
                # Generic processing
                processed_files = [self._save_to_temp(file_data, Path(file_path).suffix)]
            
            # Generate metadata
            file_metadata = self._generate_file_metadata(file_path, file_data, validation_result)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return FileProcessingResult(
                original_file=file_path,
                processed_files=processed_files,
                compression_ratio=compression_ratio,
                processing_time=processing_time,
                file_metadata=file_metadata,
                validation_result=validation_result,
                temporary_files=processed_files
            )
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def _validate_file(self, file_path: str, file_data: bytes, enable_virus_scan: bool) -> FileValidationResult:
        """Comprehensive file validation"""
        validation_errors = []
        warnings = []
        
        # Check file size
        file_size = len(file_data)
        if file_size > self.max_file_size:
            validation_errors.append(f"File size {file_size} exceeds maximum allowed size {self.max_file_size}")
        
        # Detect MIME type
        mime_type = magic.from_buffer(file_data, mime=True)
        
        # Get file extension
        file_extension = Path(file_path).suffix.lower().lstrip('.')
        
        # Validate file type
        file_type = None
        for type_name, extensions in self.supported_formats.items():
            if file_extension in extensions:
                file_type = type_name
                break
        
        if file_type is None:
            validation_errors.append(f"Unsupported file type: {file_extension}")
        
        # Virus scanning
        virus_scan_result = None
        if enable_virus_scan:
            virus_scan_result = self._scan_for_viruses(file_data)
            if virus_scan_result == "SUSPICIOUS":
                validation_errors.append("File contains suspicious content")
            elif virus_scan_result == "INFECTED":
                validation_errors.append("File appears to be infected")
        
        # Generate file hash
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # Additional validations based on file type
        if file_type == 'image':
            self._validate_image_file(file_data, validation_errors, warnings)
        elif file_type == 'document':
            self._validate_document_file(file_data, validation_errors, warnings)
        elif file_type == 'archive':
            self._validate_archive_file(file_data, validation_errors, warnings)
        
        is_valid = len(validation_errors) == 0
        
        return FileValidationResult(
            is_valid=is_valid,
            file_type=file_type or 'unknown',
            file_size=file_size,
            mime_type=mime_type,
            hash_sha256=file_hash,
            virus_scan_result=virus_scan_result,
            validation_errors=validation_errors,
            warnings=warnings
        )
    
    def _scan_for_viruses(self, file_data: bytes) -> str:
        """Basic virus scanning using signature detection"""
        try:
            # Check for known virus signatures
            for signature in self.virus_signatures:
                if signature in file_data:
                    return "INFECTED"
            
            # Check for suspicious patterns
            suspicious_patterns = [
                b'powershell', b'cmd.exe', b'regsvr32', b'rundll32',
                b'<script>', b'javascript:', b'vbscript:'
            ]
            
            suspicious_count = 0
            for pattern in suspicious_patterns:
                if pattern in file_data.lower():
                    suspicious_count += 1
            
            if suspicious_count >= 2:
                return "SUSPICIOUS"
            
            return "CLEAN"
            
        except Exception as e:
            self.logger.warning(f"Virus scan error: {e}")
            return "UNKNOWN"
    
    def _validate_image_file(self, file_data: bytes, errors: List[str], warnings: List[str]):
        """Validate image file"""
        try:
            image = Image.open(io.BytesIO(file_data))
            
            # Check image dimensions
            width, height = image.size
            if width > 10000 or height > 10000:
                warnings.append("Image dimensions are very large")
            
            # Check for transparency in JPEG
            if image.format == 'JPEG' and image.mode in ('RGBA', 'LA'):
                warnings.append("JPEG file contains transparency information")
            
        except Exception as e:
            errors.append(f"Invalid image file: {e}")
    
    def _validate_document_file(self, file_data: bytes, errors: List[str], warnings: List[str]):
        """Validate document file"""
        try:
            # Check PDF structure
            if file_data.startswith(b'%PDF'):
                # Basic PDF validation
                if b'%%EOF' not in file_data[-1024:]:
                    warnings.append("PDF file may be incomplete")
            else:
                # Check for other document formats
                if not file_data.startswith(b'PK') and not file_data.startswith(b'{\\rtf'):
                    warnings.append("Document format may not be standard")
        
        except Exception as e:
            errors.append(f"Invalid document file: {e}")
    
    def _validate_archive_file(self, file_data: bytes, errors: List[str], warnings: List[str]):
        """Validate archive file"""
        try:
            # Check ZIP structure
            if file_data.startswith(b'PK'):
                try:
                    with zipfile.ZipFile(io.BytesIO(file_data)) as zf:
                        # Check for suspicious files in archive
                        suspicious_extensions = ['.exe', '.bat', '.cmd', '.ps1', '.vbs']
                        for info in zf.infolist():
                            if any(info.filename.lower().endswith(ext) for ext in suspicious_extensions):
                                warnings.append(f"Archive contains potentially suspicious file: {info.filename}")
                except zipfile.BadZipFile:
                    errors.append("Invalid ZIP archive")
        
        except Exception as e:
            errors.append(f"Invalid archive file: {e}")
    
    def _process_image_file(self, file_data: bytes, enable_compression: bool) -> List[str]:
        """Process image file with optimization and multi-page support"""
        processed_files = []
        
        try:
            image = Image.open(io.BytesIO(file_data))
            
            # Handle multi-page images (TIFF, GIF)
            if hasattr(image, 'n_frames') and image.n_frames > 1:
                for frame_num in range(image.n_frames):
                    image.seek(frame_num)
                    frame = image.copy()
                    
                    # Optimize frame
                    if enable_compression:
                        frame = self._optimize_image(frame)
                    
                    # Save frame
                    frame_path = self._save_image_to_temp(frame, f"_frame_{frame_num}")
                    processed_files.append(frame_path)
            else:
                # Single image
                if enable_compression:
                    image = self._optimize_image(image)
                
                image_path = self._save_image_to_temp(image)
                processed_files.append(image_path)
            
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            # Fallback to original
            processed_files.append(self._save_to_temp(file_data, '.jpg'))
        
        return processed_files
    
    def _process_document_file(self, file_data: bytes, enable_compression: bool) -> List[str]:
        """Process document file with multi-page support"""
        processed_files = []
        
        try:
            # Handle PDF documents
            if file_data.startswith(b'%PDF'):
                doc = fitz.open(stream=file_data, filetype="pdf")
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    
                    # Convert page to image
                    mat = fitz.Matrix(2.0, 2.0)  # Higher resolution
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Optimize if enabled
                    if enable_compression:
                        image = self._optimize_image(image)
                    
                    # Save page
                    page_path = self._save_image_to_temp(image, f"_page_{page_num}")
                    processed_files.append(page_path)
                
                doc.close()
            else:
                # Other document types - save as is
                processed_files.append(self._save_to_temp(file_data, '.pdf'))
        
        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            # Fallback to original
            processed_files.append(self._save_to_temp(file_data, '.pdf'))
        
        return processed_files
    
    def _process_archive_file(self, file_data: bytes) -> List[str]:
        """Process archive file by extracting contents"""
        processed_files = []
        
        try:
            with zipfile.ZipFile(io.BytesIO(file_data)) as zf:
                for info in zf.infolist():
                    if not info.is_dir():
                        # Extract file
                        file_data = zf.read(info.filename)
                        
                        # Save extracted file
                        file_path = self._save_to_temp(file_data, Path(info.filename).suffix)
                        processed_files.append(file_path)
        
        except Exception as e:
            self.logger.error(f"Error processing archive: {e}")
            # Fallback to original
            processed_files.append(self._save_to_temp(file_data, '.zip'))
        
        return processed_files
    
    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """Optimize image for storage and processing"""
        try:
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Resize if too large
            max_size = (4000, 4000)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Enhance image quality
            image = ImageOps.autocontrast(image, cutoff=1)
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Image optimization error: {e}")
            return image
    
    def _save_image_to_temp(self, image: Image.Image, suffix: str = "") -> str:
        """Save image to temporary file"""
        temp_path = os.path.join(self.temp_dir, f"processed_image{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        # Save with optimization
        image.save(temp_path, 'PNG', optimize=True, compress_level=9)
        
        return temp_path
    
    def _save_to_temp(self, file_data: bytes, extension: str = "") -> str:
        """Save file data to temporary file"""
        temp_path = os.path.join(self.temp_dir, f"processed_file{extension}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        return temp_path
    
    def _generate_file_metadata(self, file_path: str, file_data: bytes, 
                              validation_result: FileValidationResult) -> Dict[str, Any]:
        """Generate comprehensive file metadata"""
        metadata = {
            'filename': Path(file_path).name,
            'file_size': validation_result.file_size,
            'file_type': validation_result.file_type,
            'mime_type': validation_result.mime_type,
            'hash_sha256': validation_result.hash_sha256,
            'processing_timestamp': datetime.now().isoformat(),
            'validation_result': {
                'is_valid': validation_result.is_valid,
                'errors': validation_result.validation_errors,
                'warnings': validation_result.warnings,
                'virus_scan': validation_result.virus_scan_result
            }
        }
        
        # Add type-specific metadata
        if validation_result.file_type == 'image':
            try:
                image = Image.open(io.BytesIO(file_data))
                metadata['image_metadata'] = {
                    'format': image.format,
                    'mode': image.mode,
                    'size': image.size,
                    'dpi': image.info.get('dpi', None),
                    'n_frames': getattr(image, 'n_frames', 1)
                }
            except Exception as e:
                metadata['image_metadata'] = {'error': str(e)}
        
        elif validation_result.file_type == 'document':
            if file_data.startswith(b'%PDF'):
                try:
                    doc = fitz.open(stream=file_data, filetype="pdf")
                    metadata['document_metadata'] = {
                        'page_count': len(doc),
                        'title': doc.metadata.get('title', ''),
                        'author': doc.metadata.get('author', ''),
                        'subject': doc.metadata.get('subject', ''),
                        'creator': doc.metadata.get('creator', '')
                    }
                    doc.close()
                except Exception as e:
                    metadata['document_metadata'] = {'error': str(e)}
        
        return metadata
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        cleaned_count = 0
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            
            try:
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
            except Exception as e:
                self.logger.warning(f"Error cleaning up {file_path}: {e}")
        
        self.logger.info(f"Cleaned up {cleaned_count} temporary files")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_size = 0
        file_count = 0
        
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except Exception:
                pass
        
        return {
            'temp_directory': self.temp_dir,
            'total_files': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'max_file_size': self.max_file_size,
            'supported_formats': self.supported_formats
        }

# Global enhanced file processor instance
enhanced_file_processor = EnhancedFileProcessor()
