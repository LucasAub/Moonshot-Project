"""
PDF to Accessible HTML Converter Server

This FastAPI server converts PDF documents to accessible HTML format with enhanced
accessibility features including OCR for images, proper semantic structure, and
accessibility scoring.

Author: Moonshot Project Team
Date: July 2025
Version: 1.0.0
"""

# Standard library imports
import asyncio
import base64
import logging
import os
import platform
import re
import tempfile
import uuid
from io import BytesIO
from typing import Any, Dict, List, Optional

# Third-party imports
import fitz  # PyMuPDF - PDF processing library
import pytesseract  # OCR (Optical Character Recognition) library
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image  # Python Imaging Library for image processing

# Configure logging for better debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Tesseract path based on the operating system
def configure_tesseract():
    """
    Configure Tesseract OCR based on the operating system.
    
    This function automatically detects the operating system and sets up
    the Tesseract OCR executable path accordingly. It handles common
    installation paths for Windows, macOS, and Linux.
    
    Raises:
        None: Function handles errors gracefully with warnings
        
    Side Effects:
        - Sets pytesseract.pytesseract.tesseract_cmd on Windows
        - Sets TESSDATA_PREFIX environment variable on macOS
        - Logs configuration status and warnings
    """
    system = platform.system().lower()
    
    if system == "windows":
        # Common Windows Tesseract installation paths
        # Check multiple possible installation locations
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', ''))
        ]
        
        # Try each path until we find a valid installation
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Found Tesseract at: {path}")
                break
        else:
            # No installation found in common paths
            logger.warning("Tesseract not found in common Windows paths. Please install Tesseract OCR.")
            
    elif system == "darwin":  # macOS
        # Set tessdata prefix for macOS (Homebrew installation)
        os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'
        if not os.path.exists(os.environ['TESSDATA_PREFIX']):
            # Try alternative paths for different macOS installations
            alt_paths = ['/usr/local/share/tessdata/', '/opt/local/share/tessdata/']
            for path in alt_paths:
                if os.path.exists(path):
                    os.environ['TESSDATA_PREFIX'] = path
                    break
    
    elif system == "linux":
        # Linux typically has Tesseract in PATH, no special configuration needed
        pass

# Initialize Tesseract OCR system
configure_tesseract()

# Verify Tesseract installation and log version information
try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {tesseract_version}")
except Exception as e:
    logger.error(f"Tesseract initialization error: {e}")
    logger.warning("OCR functionality may not work properly. Please ensure Tesseract is installed.")

# Initialize FastAPI application with metadata
app = FastAPI(
    title="PDF to Accessible HTML Converter",
    description="Convert PDF documents to accessible HTML format with OCR and accessibility features",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the frontend to communicate with the backend from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server default port
        "http://localhost:3000",  # React dev server default port
        "http://127.0.0.1:5173",  # Alternative localhost format
        "http://127.0.0.1:3000"   # Alternative localhost format
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # HTTP methods allowed
    allow_headers=["*"],  # Allow all headers
)

# Configuration constants for file validation and processing
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB maximum file size
ALLOWED_EXTENSIONS = {'.pdf'}      # Only PDF files are allowed

# Enhanced CSS for better accessibility and modern design
# This CSS provides comprehensive styling for the converted HTML documents
# with focus on accessibility, readability, and responsive design
css = """
<style>
/* Base body styling with accessibility considerations */
body { 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    font-size: 1.2em;           /* Larger font for better readability */
    line-height: 1.6;           /* Improved line spacing for readability */
    margin: 2em auto; 
    max-width: 800px;           /* Optimal reading width */
    padding: 0 1em;
    color: #333;                /* High contrast text color */ 
    background-color: #fff;
}

/* Heading styles with proper hierarchy and accessibility */
h1, h2, h3, h4, h5, h6 { 
    margin-top: 1.5em; 
    margin-bottom: 0.5em; 
    color: #2c3e50;             /* Professional dark blue */
    font-weight: 600;           /* Semi-bold for better hierarchy */
}
/* Main title styling with visual emphasis */
h1 { 
    font-size: 2.2em; 
    border-bottom: 2px solid #3498db;  /* Visual separator */
    padding-bottom: 0.2em; 
}
/* Secondary heading styling */
h2 { 
    font-size: 1.8em; 
    color: #34495e; 
}
/* Tertiary heading styling */
h3 { 
    font-size: 1.4em; 
    color: #5d6d7e; 
}

/* Paragraph styling for optimal readability */
p { 
    margin: 1em 0; 
    text-align: justify;        /* Justified text for clean appearance */
}

/* Table styling with accessibility and visual appeal */
table { 
    border-collapse: collapse; 
    margin: 1.5em 0; 
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);  /* Subtle shadow for depth */
}
/* Table cell styling with clear borders */
th, td { 
    border: 1px solid #ddd; 
    padding: 8px 12px; 
    text-align: left;
}
/* Table header styling for distinction */
th {
    background-color: #f8f9fa;  /* Light background for headers */
    font-weight: 600;           /* Bold headers */
}

/* List styling for better visual hierarchy */
ul, ol { 
    margin: 1em 0; 
    padding-left: 2em; 
    line-height: 1.8;           /* Increased line height for readability */
}
/* List item spacing */
li { 
    margin: 0.3em 0; 
}

/* Image styling with responsive design */
img { 
    max-width: 100%;            /* Responsive images */
    height: auto;               /* Maintain aspect ratio */
    border-radius: 4px;         /* Rounded corners */
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);  /* Subtle shadow */
}

/* Figure container for images with captions */
figure { 
    margin: 1.5em 0; 
    text-align: center;         /* Center-aligned images */
}
/* Caption styling for image descriptions */
figcaption { 
    font-size: 0.9em; 
    color: #666;                /* Muted color for captions */
    font-style: italic;         /* Italic style for distinction */
    margin-top: 0.5em;
}

/* Link styling with accessibility focus indicators */
a { 
    color: #3498db;             /* Blue color for links */
    text-decoration: none;      /* Remove default underline */
    border-bottom: 1px solid transparent;  /* Invisible border for smooth transition */
    transition: border-bottom-color 0.2s;  /* Smooth hover effect */
}
/* Link hover and focus states for accessibility */
a:hover, a:focus {
    border-bottom-color: #3498db;  /* Visible underline on interaction */
    outline: 2px solid #3498db;    /* Focus indicator for keyboard navigation */
    outline-offset: 2px;           /* Space between element and outline */
}

/* Section styling for document structure */
section {
    margin: 2em 0;
    padding: 1em 0;
}

/* Page break styling for multi-page documents */
.page-break {
    page-break-before: always;     /* Force page break when printing */
    border-top: 2px dashed #ccc;   /* Visual separator between pages */
    margin-top: 2em;
    padding-top: 1em;
}
</style>
"""

def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file for security and format compliance.
    
    Performs comprehensive validation of uploaded files including:
    - Presence of filename
    - File extension validation
    - Security checks for allowed file types
    
    Args:
        file (UploadFile): The uploaded file object from FastAPI
        
    Raises:
        HTTPException: 400 status code if validation fails
            - When no file is provided (filename is None)
            - When file extension is not in ALLOWED_EXTENSIONS
            
    Note:
        File extension checking is case-insensitive for user convenience
    """
    # Check if a file was actually provided
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Extract and validate file extension (case-insensitive)
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )

def safe_ocr_extract(image: Image.Image, lang: str = "eng") -> str:
    """
    Safely extract text from image using OCR with error handling.
    
    This function performs Optical Character Recognition (OCR) on an image
    with comprehensive error handling and fallback text generation.
    
    Args:
        image (Image.Image): PIL Image object to extract text from
        lang (str, optional): OCR language code. Defaults to "eng" (English).
                              Can be "fra" for French, "spa" for Spanish, etc.
                              
    Returns:
        str: Extracted text from the image, or fallback message if:
             - OCR extraction fails
             - No text is detected in the image
             - Image processing encounters an error
             
    Note:
        The function uses French fallback text ("Image sans texte détectable")
        as this appears to be designed for French document processing.
    """
    try:
        # Attempt OCR text extraction with specified language
        text = pytesseract.image_to_string(image, lang=lang).strip()
        
        # Return extracted text or fallback if empty
        return text if text else "Image sans texte détectable"
        
    except Exception as e:
        # Log the error for debugging but don't raise to maintain robustness
        logger.warning(f"OCR extraction failed: {e}")
        return "Image sans texte détectable"

def calculate_accessibility_score(html_content: str) -> tuple[int, List[str]]:
    """
    Calculate accessibility score and generate warnings for HTML content.
    
    This function analyzes HTML content for accessibility compliance and assigns
    a score from 0-100 based on various accessibility criteria. It also provides
    specific warnings for accessibility issues found.
    
    Scoring Criteria:
    - Images without alt text: -5 points per image (max -20)
    - Missing H1 title: -10 points
    - Multiple H1 titles: -5 points
    - Tables without accessibility attributes: -5 points per table (max -15)
    - Generic link text: -2 points per link (max -10)
    - Missing section structure: -5 points
    
    Args:
        html_content (str): The HTML content to analyze for accessibility
        
    Returns:
        tuple[int, List[str]]: A tuple containing:
            - int: Accessibility score (0-100, where 100 is perfect)
            - List[str]: List of warning messages in French describing issues found
            
    Note:
        The function uses French warning messages, suggesting it's designed
        for French document processing workflows.
    """
    score = 100  # Start with perfect score and deduct points for issues
    warnings = []
    
    # Check for images without alt text (accessibility barrier)
    img_tags = re.findall(r'<img[^>]*>', html_content)
    img_without_alt = [img for img in img_tags if 'alt=' not in img]
    if img_without_alt:
        # Deduct points with a maximum penalty of 20 points
        score -= min(20, len(img_without_alt) * 5)
        warnings.append(f"{len(img_without_alt)} image(s) manquent de description (attribut alt)")
    
    # Check for proper heading structure (critical for screen readers)
    header_counts = {
        'h1': len(re.findall(r'<h1[^>]*>', html_content)),
        'h2': len(re.findall(r'<h2[^>]*>', html_content)),
        'h3': len(re.findall(r'<h3[^>]*>', html_content)),
    }
    
    # Document should have exactly one H1 title
    if header_counts['h1'] == 0:
        score -= 10
        warnings.append("Document sans titre principal (H1)")
    elif header_counts['h1'] > 1:
        score -= 5
        warnings.append("Plusieurs titres H1 détectés - structure peu claire")
    
    # Check for tables without proper accessibility attributes
    table_tags = re.findall(r'<table[^>]*>', html_content)
    tables_without_accessibility = [table for table in table_tags if 'role=' not in table and 'aria-label=' not in table]
    if tables_without_accessibility:
        # Deduct points with a maximum penalty of 15 points
        score -= min(15, len(tables_without_accessibility) * 5)
        warnings.append(f"{len(tables_without_accessibility)} tableau(x) sans attributs d'accessibilité")
    
    # Check for links without descriptive text (problematic for screen readers)
    link_matches = re.findall(r'<a[^>]*href="[^"]*"[^>]*>([^<]*)</a>', html_content)
    generic_links = [link for link in link_matches if link.lower().strip() in ['cliquez ici', 'ici', 'lien', 'plus', 'voir']]
    if generic_links:
        # Deduct points with a maximum penalty of 10 points
        score -= min(10, len(generic_links) * 2)
        warnings.append(f"{len(generic_links)} lien(s) avec texte peu descriptif")
    
    # Check for document structure (sections improve navigation)
    if '<section' not in html_content:
        score -= 5
        warnings.append("Document sans structure de sections claire")
    
    # Ensure score never goes below 0
    return max(0, score), warnings

def is_big_title(block: Dict[str, Any], doc) -> bool:
    """
    Determine if a text block represents a title based on multiple heuristics.
    
    This enhanced function uses various criteria to identify titles, including:
    - Font size analysis (original method)
    - Font weight/boldness detection
    - Text length and structure analysis
    - Position analysis (top of page positioning)
    - Case analysis (all caps, title case)
    - Numbered section detection (e.g., "2.2", "1.3.4")
    - Special formatting indicators
    
    Args:
        block (Dict[str, Any]): Text block dictionary from PyMuPDF containing:
            - 'type': Block type (must be 0 for text blocks)
            - 'lines': List of line dictionaries with span information
            - 'bbox': Bounding box coordinates
        doc: PyMuPDF document object for context analysis
        
    Returns:
        bool: True if the block appears to be a title based on multiple criteria,
              False otherwise
              
    Enhanced Algorithm:
        1. Font size comparison (original method)
        2. Bold/weight detection
        3. Text length analysis (titles are typically shorter)
        4. Position analysis (titles often at top of pages)
        5. Case pattern analysis (ALL CAPS, Title Case)
        6. Numbered section detection (2.2, 1.3.4, etc.)
        7. Isolation analysis (standalone blocks)
        8. Content pattern matching
    """
    # Only process text blocks that contain lines
    if block['type'] != 0 or len(block['lines']) == 0:
        return False
    
    try:
        # Extract text content and basic properties
        block_text = ""
        font_sizes = []
        font_weights = []
        is_bold_detected = False
        
        for line in block['lines']:
            for span in line['spans']:
                text = span.get('text', '').strip()
                block_text += text + " "
                
                if 'size' in span:
                    font_sizes.append(span['size'])
                
                # Check for bold indicators in font flags or font name
                flags = span.get('flags', 0)
                font_name = span.get('font', '').lower()
                
                # Font flags bit 4 indicates bold in PyMuPDF
                if flags & 16:  # Bold flag
                    is_bold_detected = True
                
                # Check font name for bold indicators
                if any(bold_indicator in font_name for bold_indicator in ['bold', 'heavy', 'black', 'medium']):
                    is_bold_detected = True
        
        block_text = block_text.strip()
        if not block_text or not font_sizes:
            return False
        
        # 1. Font size analysis (original method with lenient threshold)
        max_font = max(font_sizes)
        all_font_sizes = []
        for page in doc:
            for page_block in page.get_text("dict")["blocks"]:
                if page_block['type'] == 0:
                    for line in page_block['lines']:
                        for span in line['spans']:
                            if 'size' in span:
                                all_font_sizes.append(span['size'])
        
        title_score = 0
        
        if all_font_sizes:
            max_doc_font = max(all_font_sizes)
            avg_doc_font = sum(all_font_sizes) / len(all_font_sizes)
            
            # Score based on font size relative to document
            if max_font >= max_doc_font - 0.5:
                title_score += 3  # Large font bonus
            elif max_font >= avg_doc_font + 1:
                title_score += 2  # Above average font bonus
            elif max_font >= avg_doc_font:
                title_score += 1  # Average or slightly above
        
        # 2. Bold/weight detection
        if is_bold_detected:
            title_score += 2
        
        # 3. Text length analysis (titles are typically shorter)
        text_length = len(block_text)
        if text_length <= 60:  # Short text more likely to be title
            title_score += 2
        elif text_length <= 100:
            title_score += 1
        
        # 4. Position analysis (titles often at top of pages)
        bbox = block.get('bbox', [0, 0, 0, 0])
        if len(bbox) >= 4:
            y_position = bbox[1]  # Top Y coordinate
            
            # Get page height for relative positioning
            page_height = 792  # Default page height, will be updated if available
            try:
                # Try to get actual page dimensions
                for page in doc:
                    page_rect = page.rect
                    page_height = page_rect.height
                    break
            except:
                pass
            
            # Check if block is in upper portion of page
            relative_position = y_position / page_height if page_height > 0 else 0
            if relative_position <= 0.2:  # Top 20% of page
                title_score += 2
            elif relative_position <= 0.4:  # Top 40% of page
                title_score += 1
        
        # 5. Case pattern analysis
        # Check for ALL CAPS (common for titles)
        if block_text.isupper() and len(block_text) > 3:
            title_score += 2
        
        # Check for Title Case (first letter of each word capitalized)
        words = block_text.split()
        if len(words) >= 2:
            title_case_words = sum(1 for word in words if word and word[0].isupper())
            if title_case_words >= len(words) * 0.7:  # 70% of words are title case
                title_score += 1
        
        # 6. Numbered section detection (e.g., "2.2", "1.3.4", "A.1")
        numbered_section_patterns = [
            r'^\d+\.\d+',           # 2.2, 1.3, 10.1
            r'^\d+\.\d+\.\d+',      # 2.2.1, 1.3.4, 10.1.2
            r'^\d+\.\d+\.\d+\.\d+', # 2.2.1.1, 1.3.4.2
            r'^[A-Z]\.\d+',         # A.1, B.2, C.3
            r'^\d+\)',              # 1), 2), 3)
            r'^\([a-z]\)',          # (a), (b), (c)
            r'^\([A-Z]\)',          # (A), (B), (C)
            r'^\d+\.',              # 1., 2., 3. (simple numbered list)
        ]
        
        for pattern in numbered_section_patterns:
            if re.match(pattern, block_text):
                title_score += 3  # Strong indicator of a title/section
                break
        
        # 7. Isolation analysis (standalone blocks often titles)
        # This is a simplified check - in practice, you might want to analyze surrounding blocks
        if text_length < 150 and '\n' not in block_text:
            title_score += 1
        
        # 8. Content pattern matching
        # Check for common title patterns
        title_patterns = [
            r'^(chapter|chapitre)\s+\d+',  # Chapter numbers
            r'^(section|partie)\s+\d+',   # Section numbers
            r'^[A-Z][A-Z\s]{2,}$',       # All caps titles
            r'^\w+(\s+\w+){0,4}:?\s*$'   # Short phrases possibly ending with colon
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, block_text, re.IGNORECASE):
                title_score += 2  # Moderate bonus for title patterns
                break
        
        # Decision threshold: require minimum score of 3 to be considered a title
        # This allows for titles that don't have large fonts but have other title characteristics
        return title_score >= 3
        
    except (KeyError, ValueError) as e:
        # Log error for debugging but don't crash the conversion process
        logger.warning(f"Error in enhanced title detection: {e}")
        return False

def process_text_block(block: Dict[str, Any], html_output: List[str], find_link_for_span, doc) -> None:
    """
    Process a text block from PDF and convert it to appropriate HTML markup.
    
    This function handles the conversion of PDF text blocks into semantic HTML,
    including link detection, bullet point processing, and title identification.
    
    Args:
        block (Dict[str, Any]): PDF text block containing lines and spans
        html_output (List[str]): List to append generated HTML strings to
        find_link_for_span: Function to find URL links for text spans
        doc: PyMuPDF document object for title detection context
        
    Side Effects:
        - Modifies html_output list by appending HTML markup
        - Processes bullet points into HTML unordered lists
        - Converts URLs in text to clickable links
        - Applies appropriate semantic tags (h3, p, ul, li)
        
    Text Processing Features:
        - Bullet point detection and list creation
        - Automatic URL link conversion
        - Link detection from PDF annotations
        - Title vs paragraph determination
        - Unicode bullet character normalization
    """
    content = []
    
    # Extract and process all text spans from the block
    for line in block["lines"]:
        for span in line["spans"]:
            text = span.get("text", "").strip()
            if not text:
                continue  # Skip empty spans
                
            # Normalize bullet point characters for consistency
            text = text.replace('\u2022', '•').replace('\uf0b7', '•')
            
            # Check for existing PDF links (annotations)
            link = find_link_for_span(span.get("bbox", [0, 0, 0, 0]))
            if link:
                # Wrap linked text in anchor tags with security attributes
                text = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{text}</a>'
            else:
                # Detect and convert URLs in plain text to clickable links
                url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
                url_matches = re.findall(url_pattern, text)
                for url_match in url_matches:
                    # Ensure URL has protocol for proper linking
                    full_url = url_match if url_match.startswith('http') else f'http://{url_match}'
                    text = text.replace(url_match, f'<a href="{full_url}" target="_blank" rel="noopener noreferrer">{url_match}</a>')
            
            content.append(text)
    
    # Combine all text content from the block
    content_text = " ".join(content).strip()
    if not content_text:
        return  # Nothing to process
    
    # Handle bullet point lists by converting to HTML unordered lists
    if '•' in content_text:
        # Split on bullet points and create list items
        items = [item.strip() for item in content_text.split('•') if item.strip()]
        if len(items) > 1:  # Only create list if multiple items exist
            html_output.append('<ul>')
            for item in items:
                if item:  # Skip empty items
                    html_output.append(f'<li>{item}</li>')
            html_output.append('</ul>')
            return
    
    # Determine appropriate HTML tag based on content analysis
    # Use h3 for titles, p for regular paragraphs
    tag = "h3" if is_big_title(block, doc) else "p"
    html_output.append(f'<{tag}>{content_text}</{tag}>')

def process_image_block(block: Dict[str, Any], html_output: List[str]) -> None:
    """
    Process an image block from PDF and convert it to accessible HTML.
    
    This function extracts images from PDF blocks, converts them to base64
    encoded data URLs, performs OCR for accessibility, and generates proper
    HTML markup with alt text and captions.
    
    Args:
        block (Dict[str, Any]): PDF image block containing raw image data
        html_output (List[str]): List to append generated HTML strings to
        
    Side Effects:
        - Modifies html_output list by appending HTML figure markup
        - Performs OCR text extraction for accessibility
        - Converts image to base64 for embedding in HTML
        - Logs warnings for processing errors
        
    Image Processing Features:
        - Base64 encoding for direct HTML embedding
        - OCR text extraction for alt text generation
        - Proper semantic markup with figure/figcaption
        - Error handling with fallback content
        - Format preservation (PNG, JPEG, etc.)
        - Accessibility compliance with ARIA roles
    """
    try:
        # Extract raw image data from the PDF block
        raw = block.get("image")
        if not raw:
            return  # No image data to process
        
        # Convert raw bytes to PIL Image object for processing
        pil_img = Image.open(BytesIO(raw))
        
        # Convert image to base64 for HTML embedding
        buffer = BytesIO()
        # Preserve original format, default to PNG if unknown
        img_format = pil_img.format if pil_img.format else 'PNG'
        pil_img.save(buffer, format=img_format)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Determine MIME type for data URL
        mime_type = f"image/{img_format.lower()}"
        
        # Extract alt text using OCR for accessibility compliance
        # Using French language for OCR to match document context
        alt_text = safe_ocr_extract(pil_img, lang="fra")
        
        # Generate accessible HTML markup with proper semantic structure
        html_output.append(
            '<figure role="img">'  # ARIA role for better accessibility
            f'<img src="data:{mime_type};base64,{img_base64}" alt="{alt_text}" loading="lazy">'  # Lazy loading for performance
            f'<figcaption>{alt_text}</figcaption>'  # Caption for additional context
            '</figure>'
        )
        
    except Exception as e:
        # Log error for debugging but don't crash the conversion
        logger.warning(f"Error processing image: {e}")
        # Provide fallback content for failed image processing
        html_output.append('<p><em>[Image non disponible]</em></p>')

def pdf_to_accessible_html(pdf_path: str) -> tuple[str, str]:
    """
    Convert PDF document to accessible HTML with comprehensive error handling.
    
    This is the main conversion function that orchestrates the entire PDF to HTML
    conversion process, including metadata extraction, page processing, text and
    image handling, and HTML document generation.
    
    Args:
        pdf_path (str): Absolute path to the PDF file to convert
        
    Returns:
        tuple[str, str]: A tuple containing:
            - str: Complete HTML document as a string with embedded CSS and content
            - str: Document title extracted from metadata or derived from filename
            
    Raises:
        HTTPException: 500 status code if conversion fails with detailed error message
        
    Conversion Process:
        1. Open and validate PDF document
        2. Extract metadata (title, etc.)
        3. Generate HTML document structure with CSS
        4. Process each page sequentially
        5. Extract and convert text blocks and images
        6. Handle links and accessibility features
        7. Generate final HTML document
        
    Features:
        - Comprehensive error handling per page
        - Accessibility-focused HTML generation
        - Image OCR for alt text
        - Link preservation from PDF
        - Proper semantic HTML structure
        - Page break indicators
        - Resource cleanup (document closure)
    """
    doc = None
    try:
        # Open the PDF document using PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Extract document metadata for title and other information
        title = doc.metadata.get('title', '').strip()
        if not title:
            # Fallback: use filename as title if no metadata title exists
            title = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Generate initial HTML document structure with accessibility features
        html_output = [
            f'<!DOCTYPE html>',                    # HTML5 doctype
            f'<html lang="fr">',                   # French language for accessibility
            f'<head>',
            f'<meta charset="UTF-8">',             # UTF-8 encoding for international characters
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">',  # Responsive design
            f'<title>{title} - Version Accessible</title>',  # Descriptive title
            css,                                   # Embedded CSS for styling
            f'</head>',
            f'<body>',
            f'<header>',
            f'<h1>{title}</h1>',                   # Main document title (H1)
            f'<p><em>Document converti en format accessible</em></p>',  # Conversion notice
            f'</header>',
            f'<main>'                              # Main content container
        ]

        total_pages = len(doc)
        logger.info(f"Processing PDF with {total_pages} pages")

        # Process each page of the PDF document
        for page_num, page in enumerate(doc, start=1):
            logger.info(f"Processing page {page_num}/{total_pages}")
            
            # Add page break separator for multi-page documents (skip for first page)
            if page_num > 1:
                html_output.append(f'<div class="page-break" aria-label="Nouvelle page"></div>')
            
            # Create semantic section for each page with ARIA label
            html_output.append(f'<section aria-label="Page {page_num} sur {total_pages}">')
            html_output.append(f'<h2>Page {page_num}</h2>')  # Page heading for navigation
            
            try:
                # Extract all blocks from the page and sort by position
                # This ensures content appears in proper reading order
                blocks = sorted(
                    page.get_text("dict")["blocks"],
                    key=lambda b: (b.get("bbox", [0, 0, 0, 0])[1], b.get("bbox", [0, 0, 0, 0])[0])
                )

                # Extract link information for clickable content preservation
                links = page.get_links()
                links_zones = []
                for link in links:
                    # Only process URI links (external links)
                    if link.get('kind') == 2 and 'uri' in link:
                        links_zones.append((link['from'], link['uri']))

                def find_link_for_span(span_bbox):
                    """
                    Find corresponding URL for a text span based on bounding box overlap.
                    
                    Args:
                        span_bbox: Bounding box coordinates [x0, y0, x1, y1] of text span
                        
                    Returns:
                        str or None: URL if span overlaps with a link zone, None otherwise
                    """
                    for bbox, uri in links_zones:
                        x0, y0, x1, y1 = bbox
                        sx0, sy0, sx1, sy1 = span_bbox
                        # Calculate center point of span for overlap detection
                        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
                        # Check if span center falls within link bounding box
                        if x0 <= cx <= x1 and y0 <= cy <= y1:
                            return uri
                    return None

                # Process each block on the page (text or image)
                for block in blocks:
                    try:
                        if block["type"] == 0:  # Text block
                            process_text_block(block, html_output, find_link_for_span, doc)
                        elif block["type"] == 1:  # Image block
                            process_image_block(block, html_output)
                    except Exception as e:
                        # Log block-level errors but continue processing
                        logger.warning(f"Error processing block on page {page_num}: {e}")
                        continue

            except Exception as e:
                # Log page-level errors and add error message to output
                logger.error(f"Error processing page {page_num}: {e}")
                html_output.append(f'<p><em>Erreur lors du traitement de la page {page_num}</em></p>')

            html_output.append('</section>')  # Close page section

        # Complete the HTML document structure
        html_output.extend(['</main>', '</body>', '</html>'])
        
        # Join all HTML parts and return with title
        return "\n".join(html_output), title

    except Exception as e:
        # Handle document-level errors
        logger.error(f"Error converting PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la conversion du PDF: {str(e)}")
    finally:
        # Ensure PDF document is properly closed to free resources
        if doc:
            doc.close()

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """
    Convert uploaded PDF to accessible HTML format.
    
    This is the main API endpoint that handles PDF file uploads and converts
    them to accessible HTML with comprehensive error handling and validation.
    
    Args:
        file (UploadFile): PDF file uploaded via multipart form data
        
    Returns:
        dict: JSON response containing:
            - html (str): Complete HTML document with embedded CSS and content
            - title (str): Document title from metadata or filename
            - accessibilityScore (int): Accessibility score from 0-100
            - warnings (List[str]): List of accessibility warnings in French
            
    Raises:
        HTTPException: Various status codes for different error conditions:
            - 400: Invalid file type, missing file, or file too large
            - 500: Internal server error during conversion
            
    Process Flow:
        1. Log file reception for monitoring
        2. Validate file type and presence
        3. Check file size limits
        4. Create secure temporary file
        5. Convert PDF to HTML
        6. Calculate accessibility score
        7. Return results with cleanup
        
    Security Features:
        - File type validation (PDF only)
        - File size limits (50MB max)
        - Temporary file handling with cleanup
        - Input sanitization
    """
    logger.info(f"Received file: {file.filename}")
    
    # Validate file type and presence
    validate_file(file)
    
    # Read file contents and check size limits
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Create secure temporary file for processing
    # Using delete=False to manually control cleanup
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        # Convert PDF to accessible HTML
        html_content, title = pdf_to_accessible_html(tmp_path)
        
        # Analyze HTML for accessibility compliance and scoring
        score, warnings = calculate_accessibility_score(html_content)
        
        logger.info(f"Conversion completed for {file.filename}. Score: {score}")
        
        # Return comprehensive conversion results
        return {
            "html": html_content,
            "title": title,
            "accessibilityScore": score,
            "warnings": warnings
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Handle unexpected errors with generic error message
        logger.error(f"Unexpected error converting {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
    finally:
        # Always clean up temporary file, even if an error occurs
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring and availability verification.
    
    This endpoint provides a simple way to verify that the PDF conversion
    service is running and responsive. It's typically used by:
    - Load balancers for health checking
    - Monitoring systems for uptime verification
    - Development tools for service discovery
    - CI/CD pipelines for deployment validation
    
    Returns:
        dict: JSON response containing:
            - status (str): "healthy" if service is operational
            - message (str): Descriptive message about service status
            
    HTTP Status: Always returns 200 OK if the service is running
    
    Note:
        This is a lightweight endpoint that doesn't perform intensive
        operations, making it suitable for frequent health checks.
    """
    return {
        "status": "healthy",
        "message": "PDF to HTML conversion service is running"
    }

# Application entry point for direct execution
if __name__ == "__main__":
    # Import uvicorn server for running the application
    import uvicorn
    
    # Run the FastAPI application
    # host="0.0.0.0" makes the server accessible from any IP address
    # port=8000 is the default port for the service
    uvicorn.run(app, host="0.0.0.0", port=8000)
