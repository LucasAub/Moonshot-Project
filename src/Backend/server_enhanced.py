from fastapi import FastAPI, UploadFile, HTTPException, File
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import uuid
import re
from io import BytesIO
import tempfile
import os
import logging
import base64
import platform
from typing import Optional, List, Dict, Any
import asyncio


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Tesseract path based on the operating system
def configure_tesseract():
    """Configure Tesseract OCR based on the operating system."""
    system = platform.system().lower()
    
    if system == "windows":
        # Common Windows Tesseract installation paths
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', ''))
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Found Tesseract at: {path}")
                break
        else:
            logger.warning("Tesseract not found in common Windows paths. Please install Tesseract OCR.")
            
    elif system == "darwin":  # macOS
        os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'
        if not os.path.exists(os.environ['TESSDATA_PREFIX']):
            # Try alternative paths
            alt_paths = ['/usr/local/share/tessdata/', '/opt/local/share/tessdata/']
            for path in alt_paths:
                if os.path.exists(path):
                    os.environ['TESSDATA_PREFIX'] = path
                    break
    
    elif system == "linux":
        # Linux typically has Tesseract in PATH
        pass

# Initialize Tesseract
configure_tesseract()

try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {tesseract_version}")
except Exception as e:
    logger.error(f"Tesseract initialization error: {e}")
    logger.warning("OCR functionality may not work properly. Please ensure Tesseract is installed.")

app = FastAPI(
    title="PDF to Accessible HTML Converter",
    description="Convert PDF documents to accessible HTML format",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.pdf'}

# Enhanced CSS for better accessibility and readability
css = """
<style>
body { 
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    font-size: 1.2em; 
    line-height: 1.6; 
    margin: 2em auto; 
    max-width: 800px; 
    padding: 0 1em;
    color: #333; 
    background-color: #fff;
}
h1, h2, h3, h4, h5, h6 { 
    margin-top: 1.5em; 
    margin-bottom: 0.5em; 
    color: #2c3e50;
    font-weight: 600;
}
h1 { font-size: 2.2em; border-bottom: 2px solid #3498db; padding-bottom: 0.2em; }
h2 { font-size: 1.8em; color: #34495e; }
h3 { font-size: 1.4em; color: #5d6d7e; }
p { 
    margin: 1em 0; 
    text-align: justify;
}
table { 
    border-collapse: collapse; 
    margin: 1.5em 0; 
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
th, td { 
    border: 1px solid #ddd; 
    padding: 8px 12px; 
    text-align: left;
}
th {
    background-color: #f8f9fa;
    font-weight: 600;
}
ul, ol { 
    margin: 1em 0; 
    padding-left: 2em; 
    line-height: 1.8;
}
li { 
    margin: 0.3em 0; 
}
img { 
    max-width: 100%; 
    height: auto; 
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
figure { 
    margin: 1.5em 0; 
    text-align: center;
}
figcaption { 
    font-size: 0.9em; 
    color: #666; 
    font-style: italic;
    margin-top: 0.5em;
}
a { 
    color: #3498db; 
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-bottom-color 0.2s;
}
a:hover, a:focus {
    border-bottom-color: #3498db;
    outline: 2px solid #3498db;
    outline-offset: 2px;
}
section {
    margin: 2em 0;
    padding: 1em 0;
}
.page-break {
    page-break-before: always;
    border-top: 2px dashed #ccc;
    margin-top: 2em;
    padding-top: 1em;
}
</style>
"""

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )

def safe_ocr_extract(image: Image.Image, lang: str = "eng") -> str:
    """Safely extract text from image using OCR."""
    try:
        text = pytesseract.image_to_string(image, lang=lang).strip()
        return text if text else "Image sans texte détectable"
    except Exception as e:
        logger.warning(f"OCR extraction failed: {e}")
        return "Image sans texte détectable"

def calculate_accessibility_score(html_content: str) -> tuple[int, List[str]]:
    """Calculate accessibility score and return warnings."""
    score = 100
    warnings = []
    
    # Check for images without alt text
    img_tags = re.findall(r'<img[^>]*>', html_content)
    img_without_alt = [img for img in img_tags if 'alt=' not in img]
    if img_without_alt:
        score -= min(20, len(img_without_alt) * 5)
        warnings.append(f"{len(img_without_alt)} image(s) manquent de description (attribut alt)")
    
    # Check for proper heading structure
    header_counts = {
        'h1': len(re.findall(r'<h1[^>]*>', html_content)),
        'h2': len(re.findall(r'<h2[^>]*>', html_content)),
        'h3': len(re.findall(r'<h3[^>]*>', html_content)),
    }
    
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
        score -= min(15, len(tables_without_accessibility) * 5)
        warnings.append(f"{len(tables_without_accessibility)} tableau(x) sans attributs d'accessibilité")
    
    # Check for links without descriptive text
    link_matches = re.findall(r'<a[^>]*href="[^"]*"[^>]*>([^<]*)</a>', html_content)
    generic_links = [link for link in link_matches if link.lower().strip() in ['cliquez ici', 'ici', 'lien', 'plus', 'voir']]
    if generic_links:
        score -= min(10, len(generic_links) * 2)
        warnings.append(f"{len(generic_links)} lien(s) avec texte peu descriptif")
    
    # Check for document structure
    if '<section' not in html_content:
        score -= 5
        warnings.append("Document sans structure de sections claire")
    
    return max(0, score), warnings

def is_big_title(block: Dict[str, Any], doc) -> bool:
    """Detection of big titles based on font size."""
    if block['type'] != 0 or len(block['lines']) == 0:
        return False
    
    try:
        max_font = max(
            span['size']
            for line in block['lines']
            for span in line['spans']
            if 'size' in span
        )
        
        all_font_sizes = []
        for p in doc:
            for b in p.get_text("dict")["blocks"]:
                if b['type'] == 0:
                    for l in b['lines']:
                        for span in l['spans']:
                            if 'size' in span:
                                all_font_sizes.append(span['size'])
        
        if not all_font_sizes:
            return False
            
        max_doc_font = max(all_font_sizes)
        return max_font >= max_doc_font - 0.5  # More lenient threshold
        
    except (KeyError, ValueError) as e:
        logger.warning(f"Error in title detection: {e}")
        return False

def process_text_block(block: Dict[str, Any], html_output: List[str], find_link_for_span, doc) -> None:
    """Process a text block and add it to HTML output."""
    content = []
    
    for line in block["lines"]:
        for span in line["spans"]:
            text = span.get("text", "").strip()
            if not text:
                continue
                
            # Clean up bullet point characters
            text = text.replace('\u2022', '•').replace('\uf0b7', '•')
            
            # Check for links
            link = find_link_for_span(span.get("bbox", [0, 0, 0, 0]))
            if link:
                text = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{text}</a>'
            else:
                # Check for URLs in text and make them clickable
                url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
                url_matches = re.findall(url_pattern, text)
                for url_match in url_matches:
                    full_url = url_match if url_match.startswith('http') else f'http://{url_match}'
                    text = text.replace(url_match, f'<a href="{full_url}" target="_blank" rel="noopener noreferrer">{url_match}</a>')
            
            content.append(text)
    
    content_text = " ".join(content).strip()
    if not content_text:
        return
    
    # Handle bullet points
    if '•' in content_text:
        items = [item.strip() for item in content_text.split('•') if item.strip()]
        if len(items) > 1:
            html_output.append('<ul>')
            for item in items:
                if item:  # Skip empty items
                    html_output.append(f'<li>{item}</li>')
            html_output.append('</ul>')
            return
    
    # Determine if this is a title or regular text
    tag = "h3" if is_big_title(block, doc) else "p"
    html_output.append(f'<{tag}>{content_text}</{tag}>')

def process_image_block(block: Dict[str, Any], html_output: List[str]) -> None:
    """Process an image block and add it to HTML output."""
    try:
        raw = block.get("image")
        if not raw:
            return
        
        pil_img = Image.open(BytesIO(raw))
        
        # Convert image to base64
        buffer = BytesIO()
        img_format = pil_img.format if pil_img.format else 'PNG'
        pil_img.save(buffer, format=img_format)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = f"image/{img_format.lower()}"
        
        # Extract alt text using OCR
        alt_text = safe_ocr_extract(pil_img, lang="fra")
        
        # Add image to HTML
        html_output.append(
            '<figure role="img">'
            f'<img src="data:{mime_type};base64,{img_base64}" alt="{alt_text}" loading="lazy">'
            f'<figcaption>{alt_text}</figcaption>'
            '</figure>'
        )
        
    except Exception as e:
        logger.warning(f"Error processing image: {e}")
        html_output.append('<p><em>[Image non disponible]</em></p>')

def pdf_to_accessible_html(pdf_path: str) -> tuple[str, str]:
    """Convert PDF to accessible HTML with enhanced error handling."""
    doc = None
    try:
        doc = fitz.open(pdf_path)
        
        # Get document metadata
        title = doc.metadata.get('title', '').strip()
        if not title:
            title = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Start HTML document
        html_output = [
            f'<!DOCTYPE html>',
            f'<html lang="fr">',
            f'<head>',
            f'<meta charset="UTF-8">',
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<title>{title} - Version Accessible</title>',
            css,
            f'</head>',
            f'<body>',
            f'<header>',
            f'<h1>{title}</h1>',
            f'<p><em>Document converti en format accessible</em></p>',
            f'</header>',
            f'<main>'
        ]

        total_pages = len(doc)
        logger.info(f"Processing PDF with {total_pages} pages")

        for page_num, page in enumerate(doc, start=1):
            logger.info(f"Processing page {page_num}/{total_pages}")
            
            if page_num > 1:
                html_output.append(f'<div class="page-break" aria-label="Nouvelle page"></div>')
            
            html_output.append(f'<section aria-label="Page {page_num} sur {total_pages}">')
            html_output.append(f'<h2>Page {page_num}</h2>')
            
            try:
                # Get page blocks and sort them by position
                blocks = sorted(
                    page.get_text("dict")["blocks"],
                    key=lambda b: (b.get("bbox", [0, 0, 0, 0])[1], b.get("bbox", [0, 0, 0, 0])[0])
                )

                # Extract links
                links = page.get_links()
                links_zones = []
                for link in links:
                    if link.get('kind') == 2 and 'uri' in link:
                        links_zones.append((link['from'], link['uri']))

                def find_link_for_span(span_bbox):
                    """Find link URL for a given span based on its bounding box."""
                    for bbox, uri in links_zones:
                        x0, y0, x1, y1 = bbox
                        sx0, sy0, sx1, sy1 = span_bbox
                        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
                        if x0 <= cx <= x1 and y0 <= cy <= y1:
                            return uri
                    return None

                # Process each block
                for block in blocks:
                    try:
                        if block["type"] == 0:  # Text block
                            process_text_block(block, html_output, find_link_for_span, doc)
                        elif block["type"] == 1:  # Image block
                            process_image_block(block, html_output)
                    except Exception as e:
                        logger.warning(f"Error processing block on page {page_num}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                html_output.append(f'<p><em>Erreur lors du traitement de la page {page_num}</em></p>')

            html_output.append('</section>')

        html_output.extend(['</main>', '</body>', '</html>'])
        
        return "\n".join(html_output), title

    except Exception as e:
        logger.error(f"Error converting PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la conversion du PDF: {str(e)}")
    finally:
        if doc:
            doc.close()

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """Convert uploaded PDF to accessible HTML."""
    logger.info(f"Received file: {file.filename}")
    
    # Validate file
    validate_file(file)
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        # Convert PDF to HTML
        html_content, title = pdf_to_accessible_html(tmp_path)
        
        # Calculate accessibility score
        score, warnings = calculate_accessibility_score(html_content)
        
        logger.info(f"Conversion completed for {file.filename}. Score: {score}")
        
        return {
            "html": html_content,
            "title": title,
            "accessibilityScore": score,
            "warnings": warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error converting {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "PDF to HTML conversion service is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
