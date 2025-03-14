import os
import pdfplumber
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTImage, LTTextContainer, LTFigure, LTPage

class PDFAnalyzer:
    """
    Analyzes PDF documents for accessibility issues using pdfplumber and pdfminer.six
    """
    
    def __init__(self, file_path):
        """Initialize the analyzer with a PDF file path"""
        self.file_path = file_path
        self.issues = []
        self.document_info = {
            'has_text': False,
            'has_images': False,
            'needs_ocr': False,
            'page_count': 0,
            'images': [],
            'form_fields': []
        }
    
    def analyze(self):
        """
        Perform comprehensive accessibility analysis on the PDF
        Returns a dictionary with analysis results
        """
        self._validate_file()
        self._extract_document_info()
        self._check_text_content()
        self._identify_images()
        self._check_document_structure()
        self._analyze_reading_order()
        self._check_form_fields()
        
        return {
            'issues': self.issues,
            'document_info': self.document_info
        }
    
    def _validate_file(self):
        """Validate that the file exists and is a valid PDF"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF file not found: {self.file_path}")
        
        # Check file size
        file_size = os.path.getsize(self.file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise ValueError("File size exceeds the maximum allowed (100MB)")
        
        # Validate PDF header
        with open(self.file_path, 'rb') as f:
            header = f.read(5)
            if header != b'%PDF-':
                raise ValueError("File is not a valid PDF")
    
    def _extract_document_info(self):
        """Extract basic document information"""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                self.document_info['page_count'] = len(pdf.pages)
                
                # Extract metadata if available
                if hasattr(pdf, 'metadata') and pdf.metadata:
                    metadata = pdf.metadata
                    if 'Title' in metadata and metadata['Title']:
                        self.document_info['title'] = metadata['Title']
                    else:
                        self.issues.append({
                            'type': 'missing_title',
                            'description': 'Document lacks a title in metadata',
                            'wcag': '2.4.2'
                        })
                    
                    if 'Language' in metadata and metadata['Language']:
                        self.document_info['language'] = metadata['Language']
                    else:
                        self.issues.append({
                            'type': 'missing_language',
                            'description': 'Document language is not specified',
                            'wcag': '3.1.1'
                        })
                else:
                    self.issues.append({
                        'type': 'missing_metadata',
                        'description': 'Document lacks essential metadata',
                        'wcag': '2.4.2, 3.1.1'
                    })
        except Exception as e:
            self.issues.append({
                'type': 'document_error',
                'description': f'Error analyzing document: {str(e)}',
                'wcag': 'multiple'
            })
    
    def _check_text_content(self):
        """
        Check for the presence of text content and evaluate 
        if OCR might be needed
        """
        try:
            total_text_chars = 0
            
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    total_text_chars += len(page_text)
            
            # Check if document has text
            self.document_info['has_text'] = total_text_chars > 0
            
            # Check if text density suggests OCR is needed
            # (Less than 100 chars per page on average might indicate image-based PDF)
            avg_chars_per_page = total_text_chars / max(1, self.document_info['page_count'])
            if avg_chars_per_page < 100:
                self.document_info['needs_ocr'] = True
                self.issues.append({
                    'type': 'likely_image_based',
                    'description': 'Document appears to be image-based with little machine-readable text',
                    'wcag': '1.4.5'
                })
        except Exception as e:
            self.issues.append({
                'type': 'text_extraction_error',
                'description': f'Error checking text content: {str(e)}',
                'wcag': 'multiple'
            })
    
    def _identify_images(self):
        """Identify images in the document and check for alt text"""
        try:
            image_elements = []
            
            # Use pdfminer to extract image elements
            for page_layout in extract_pages(self.file_path):
                page_num = page_layout.pageid
                
                for element in page_layout:
                    if isinstance(element, (LTImage, LTFigure)):
                        image_elements.append({
                            'page': page_num,
                            'bbox': (element.x0, element.y0, element.x1, element.y1),
                            'has_alt_text': False  # Default assumption
                        })
            
            self.document_info['has_images'] = len(image_elements) > 0
            self.document_info['images'] = image_elements
            
            if image_elements:
                self.issues.append({
                    'type': 'images_without_alt_text',
                    'description': f'Document contains {len(image_elements)} image(s) that may need alternative text',
                    'wcag': '1.1.1',
                    'affected_elements': image_elements
                })
        except Exception as e:
            self.issues.append({
                'type': 'image_analysis_error',
                'description': f'Error identifying images: {str(e)}',
                'wcag': '1.1.1'
            })
    
    def _check_document_structure(self):
        """Check for proper document structure and tagging"""
        try:
            # This is a simplified check. A comprehensive check would require
            # deeper analysis of the PDF structure with pikepdf
            structure_exists = False
            
            # For now, we'll assume structure is missing
            if not structure_exists:
                self.issues.append({
                    'type': 'missing_structure',
                    'description': 'Document lacks proper structural tags for accessibility',
                    'wcag': '1.3.1'
                })
        except Exception as e:
            self.issues.append({
                'type': 'structure_analysis_error',
                'description': f'Error checking document structure: {str(e)}',
                'wcag': '1.3.1'
            })
    
    def _analyze_reading_order(self):
        """Analyze the document for proper reading order"""
        # This is a placeholder for reading order analysis
        # A full implementation would require spatial analysis of text elements
        self.issues.append({
            'type': 'reading_order_unknown',
            'description': 'Reading order needs verification',
            'wcag': '1.3.2'
        })
    
    def _check_form_fields(self):
        """Check for form fields and their accessibility"""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                has_forms = False
                form_fields = []
                
                # Simple check for forms - this would need enhancement
                for page in pdf.pages:
                    if hasattr(page, 'annots') and page.annots:
                        for annot in page.annots:
                            if annot.get('Subtype') == 'Widget':
                                has_forms = True
                                form_fields.append({
                                    'page': page.page_number,
                                    'type': annot.get('FT', 'Unknown'),
                                    'has_label': False  # Default assumption
                                })
                
                if has_forms:
                    self.document_info['has_forms'] = True
                    self.document_info['form_fields'] = form_fields
                    
                    self.issues.append({
                        'type': 'form_fields',
                        'description': f'Document contains {len(form_fields)} form field(s) that need accessibility verification',
                        'wcag': '1.3.1, 3.3.2',
                        'affected_elements': form_fields
                    })
        except Exception as e:
            self.issues.append({
                'type': 'form_analysis_error',
                'description': f'Error checking form fields: {str(e)}',
                'wcag': '1.3.1, 3.3.2'
            })