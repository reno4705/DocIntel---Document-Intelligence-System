import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import pdf2image
import io
from typing import Union
from pathlib import Path

from app.core import logger


class OCRService:
    def __init__(self):
        # PSM 3 = Fully automatic page segmentation (better for complex layouts)
        # PSM 6 = Single uniform block (for simple documents)
        self._tesseract_config = "--oem 3 --psm 3"
        self._simple_config = "--oem 3 --psm 6"
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhanced preprocessing for better OCR accuracy."""
        # Convert to grayscale
        grayscale = image.convert("L")
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(grayscale)
        contrasted = enhancer.enhance(1.5)
        
        # Sharpen image
        sharpened = contrasted.filter(ImageFilter.SHARPEN)
        
        # Resize if too small (Tesseract works better with larger images)
        width, height = sharpened.size
        if width < 1000:
            scale = 1000 / width
            new_size = (int(width * scale), int(height * scale))
            sharpened = sharpened.resize(new_size, Image.Resampling.LANCZOS)
        
        # Binarize (convert to black and white)
        threshold = 140
        binarized = sharpened.point(lambda x: 255 if x > threshold else 0, '1')
        
        return binarized.convert("L")
    
    def _extract_from_image(self, image: Image.Image) -> str:
        processed_image = self._preprocess_image(image)
        text = pytesseract.image_to_string(processed_image, config=self._tesseract_config)
        return text.strip()
    
    def _extract_from_pdf(self, file_bytes: bytes) -> str:
        try:
            images = pdf2image.convert_from_bytes(file_bytes)
            extracted_texts = []
            for page_num, image in enumerate(images):
                logger.info(f"Processing PDF page {page_num + 1}")
                text = self._extract_from_image(image)
                extracted_texts.append(text)
            return "\n\n".join(extracted_texts)
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            raise
    
    def extract_text_from_file(self, file_bytes: bytes, file_extension: str) -> str:
        try:
            if file_extension.lower() == ".pdf":
                return self._extract_from_pdf(file_bytes)
            else:
                image = Image.open(io.BytesIO(file_bytes))
                return self._extract_from_image(image)
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise ValueError(f"Failed to extract text: {str(e)}")


ocr_service = OCRService()
