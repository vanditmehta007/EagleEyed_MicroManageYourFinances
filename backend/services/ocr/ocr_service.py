from fastapi import UploadFile
from backend.models.response_models import SuccessResponse
from backend.utils.logger import logger
import pytesseract
from PIL import Image
import io
import pdf2image

# USER INPUT REQUIRED: Ensure Tesseract OCR is installed on the system
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Uncomment and set path for Windows

# USER INPUT REQUIRED: Ensure Poppler is installed for pdf2image
# Windows: Download from http://blog.alivate.com.au/poppler-windows/ and add bin to PATH
# Linux: sudo apt-get install poppler-utils

class OCRService:
    """
    Service for OCR extraction from images and PDFs.
    """

    def extract_text(self, file: UploadFile) -> SuccessResponse:
        """
        Extract text from an image or PDF using OCR.
        """
        try:
            content = file.file.read()
            text = ""
            
            if file.content_type == "application/pdf":
                # Convert PDF to images
                images = pdf2image.convert_from_bytes(content)
                for img in images:
                    text += pytesseract.image_to_string(img) + "\n"
            else:
                # Process image directly
                image = Image.open(io.BytesIO(content))
                text = pytesseract.image_to_string(image)
            
            return SuccessResponse(success=True, data=text.strip())
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return SuccessResponse(success=False, error=str(e))

    def extract_table(self, file: UploadFile) -> SuccessResponse:
        """
        Extract tabular data from a document.
        """
        try:
            # For table extraction, we'll use a simplified approach or placeholder
            # as robust table extraction often requires specialized libraries like Tabula or Textract
            # Here we reuse text extraction as a fallback for now
            
            # In a real production setup, integrate AWS Textract or Azure Form Recognizer here
            text_response = self.extract_text(file)
            
            if not text_response.success:
                return text_response
                
            # Simple heuristic to structure text into rows (very basic)
            lines = text_response.data.split('\n')
            table_data = [line.split() for line in lines if line.strip()]
            
            return SuccessResponse(success=True, data=table_data)
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return SuccessResponse(success=False, error=str(e))
