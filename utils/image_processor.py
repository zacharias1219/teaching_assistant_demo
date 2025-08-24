import cv2
import numpy as np
import fitz  # PyMuPDF for PDF processing
from PIL import Image, ImageEnhance, ImageFilter
import io
import base64
from typing import List, Dict, Tuple, Optional
import json

class ImageProcessor:
    """Advanced image processing for OCR optimization"""
    
    def __init__(self):
        self.min_question_height = 50  # Minimum height for question detection
        self.min_question_width = 100   # Minimum width for question detection
        
    def preprocess_image(self, image_data: bytes, content_type: str = None) -> List[bytes]:
        """Preprocess image for optimal OCR performance"""
        try:
            # Convert PDF to images if needed
            if content_type == 'application/pdf':
                return self._pdf_to_images(image_data)
            else:
                # Process single image
                processed_image = self._enhance_image(image_data)
                return [processed_image]
                
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return [image_data]  # Return original if processing fails
    
    def _pdf_to_images(self, pdf_data: bytes) -> List[bytes]:
        """Convert PDF to list of image bytes"""
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            images = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Enhance the image
                enhanced_image = self._enhance_pil_image(pil_image)
                
                # Convert back to bytes
                img_buffer = io.BytesIO()
                enhanced_image.save(img_buffer, format='PNG')
                images.append(img_buffer.getvalue())
            
            pdf_document.close()
            return images
            
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            return [pdf_data]
    
    def _enhance_image(self, image_data: bytes) -> bytes:
        """Enhance single image for better OCR"""
        try:
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            enhanced_image = self._enhance_pil_image(pil_image)
            
            # Convert back to bytes
            img_buffer = io.BytesIO()
            enhanced_image.save(img_buffer, format='PNG')
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"Error enhancing image: {e}")
            return image_data
    
    def _enhance_pil_image(self, image: Image.Image) -> Image.Image:
        """Apply image enhancement techniques"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Auto-rotate based on EXIF data
            try:
                image = Image.fromarray(np.array(image))
            except:
                pass
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            return image
            
        except Exception as e:
            print(f"Error in PIL enhancement: {e}")
            return image
    
    def detect_question_boundaries(self, image_data: bytes) -> List[Dict]:
        """Detect question boundaries in image using computer vision"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            question_regions = []
            
            for contour in contours:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (minimum question size)
                if w >= self.min_question_width and h >= self.min_question_height:
                    # Calculate area ratio to filter out noise
                    area = cv2.contourArea(contour)
                    if area > 1000:  # Minimum area threshold
                        question_regions.append({
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h,
                            'area': area,
                            'confidence': min(area / (w * h), 1.0)  # Density-based confidence
                        })
            
            # Sort by y-coordinate (top to bottom)
            question_regions.sort(key=lambda x: x['y'])
            
            return question_regions
            
        except Exception as e:
            print(f"Error detecting question boundaries: {e}")
            return []
    
    def extract_roi(self, image_data: bytes, region: Dict) -> bytes:
        """Extract Region of Interest from image"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return image_data
            
            # Extract ROI
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            roi = image[y:y+h, x:x+w]
            
            # Convert back to bytes
            success, buffer = cv2.imencode('.png', roi)
            if success:
                return buffer.tobytes()
            else:
                return image_data
                
        except Exception as e:
            print(f"Error extracting ROI: {e}")
            return image_data
    
    def slice_image_by_questions(self, image_data: bytes) -> List[Dict]:
        """Slice image into individual question regions"""
        try:
            # Detect question boundaries
            question_regions = self.detect_question_boundaries(image_data)
            
            if not question_regions:
                # If no questions detected, return full image as single region
                return [{
                    'region': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    'image_data': image_data,
                    'question_number': 1,
                    'confidence': 0.5
                }]
            
            sliced_questions = []
            
            for i, region in enumerate(question_regions):
                # Extract ROI for this question
                roi_data = self.extract_roi(image_data, region)
                
                sliced_questions.append({
                    'region': region,
                    'image_data': roi_data,
                    'question_number': i + 1,
                    'confidence': region.get('confidence', 0.5)
                })
            
            return sliced_questions
            
        except Exception as e:
            print(f"Error slicing image by questions: {e}")
            return [{
                'region': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                'image_data': image_data,
                'question_number': 1,
                'confidence': 0.5
            }]
    
    def detect_page_breaks(self, image_data: bytes) -> List[int]:
        """Detect page breaks in multi-page documents"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return []
            
            height, width = image.shape[:2]
            
            # Look for horizontal lines that might indicate page breaks
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect horizontal lines
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            page_breaks = []
            
            if lines is not None:
                for line in lines:
                    rho, theta = line[0]
                    
                    # Check if line is horizontal (theta close to 0 or pi)
                    if abs(theta) < 0.1 or abs(theta - np.pi) < 0.1:
                        y_coord = int(rho)
                        
                        # Filter out lines too close to edges
                        if 50 < y_coord < height - 50:
                            page_breaks.append(y_coord)
            
            # Sort page breaks
            page_breaks.sort()
            
            return page_breaks
            
        except Exception as e:
            print(f"Error detecting page breaks: {e}")
            return []
    
    def split_by_pages(self, image_data: bytes) -> List[bytes]:
        """Split image into separate pages"""
        try:
            page_breaks = self.detect_page_breaks(image_data)
            
            if not page_breaks:
                # No page breaks detected, return single page
                return [image_data]
            
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return [image_data]
            
            height, width = image.shape[:2]
            pages = []
            
            # Split image at page breaks
            start_y = 0
            for break_y in page_breaks:
                # Extract page
                page = image[start_y:break_y, 0:width]
                
                # Convert to bytes
                success, buffer = cv2.imencode('.png', page)
                if success:
                    pages.append(buffer.tobytes())
                
                start_y = break_y
            
            # Add last page
            if start_y < height:
                page = image[start_y:height, 0:width]
                success, buffer = cv2.imencode('.png', page)
                if success:
                    pages.append(buffer.tobytes())
            
            return pages if pages else [image_data]
            
        except Exception as e:
            print(f"Error splitting by pages: {e}")
            return [image_data]
    
    def get_image_metadata(self, image_data: bytes) -> Dict:
        """Extract metadata from image"""
        try:
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            return {
                'width': pil_image.width,
                'height': pil_image.height,
                'mode': pil_image.mode,
                'format': pil_image.format,
                'size_bytes': len(image_data)
            }
            
        except Exception as e:
            print(f"Error getting image metadata: {e}")
            return {
                'width': 0,
                'height': 0,
                'mode': 'unknown',
                'format': 'unknown',
                'size_bytes': len(image_data)
            }

# Global image processor instance
image_processor = ImageProcessor()
