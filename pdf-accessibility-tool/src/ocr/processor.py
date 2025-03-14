import os
import tempfile
import pytesseract
from PIL import Image
import fitz  # PyMuPDF

class OCRProcessor:
    """
    Processes image-based PDFs using Tesseract OCR
    """
    
    def __init__(self):
        """Initialize the OCR processor"""
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    
    def process_pdf(self, pdf_path):
        """
        Process a PDF file with OCR
        Returns text content by page
        """
        text_by_page = {}
        
        try:
            # Open the PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Process each page
            for page_num, page in enumerate(doc):
                # Get page as image
                pix = page.get_pixmap()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_path = temp_file.name
                    pix.save(temp_path)
                
                try:
                    # Use Tesseract to extract text
                    text = pytesseract.image_to_string(Image.open(temp_path))
                    text_by_page[page_num] = text
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            return text_by_page
        
        except Exception as e:
            raise RuntimeError(f"OCR processing error: {str(e)}")
    
    def get_word_data(self, image_path):
        """
        Get detailed word data including positions
        Useful for creating text overlays
        """
        try:
            data = pytesseract.image_to_data(
                Image.open(image_path),
                output_type=pytesseract.Output.DICT
            )
            return data
        except Exception as e:
            raise RuntimeError(f"Word data extraction error: {str(e)}")