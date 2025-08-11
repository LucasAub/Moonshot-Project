"""
PDF to HTML Converter Server - Enhanced Version
FastAPI server that converts PDF files to accessible HTML format.
See CODE_DOCUMENTATION.md for detailed architecture documentation.
"""

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tesseract OCR Configuration - Multi-platform setup
if platform.system() == "Windows":
    # Check common Windows installation paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
    ]
    
    tesseract_found = False
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_found = True
            logger.info(f"Tesseract found at: {path}")
            break
    
    if not tesseract_found:
        logger.warning("Tesseract not found. OCR will be disabled.")
else:
    # macOS/Linux configuration
    os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'

# Test Tesseract availability
tesseract_available = False
try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {tesseract_version}")
    tesseract_available = True
except Exception as e:
    logger.warning(f"Tesseract not available: {e}")
    tesseract_available = False

# FastAPI Application Setup
app = FastAPI(title="PDF to HTML Converter", version="1.0.0")

# Global exception handler - ensures all errors return valid JSON
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch unhandled exceptions and return JSON responses"""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": "internal_server_error"
        }
    )

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CSS styles for accessible HTML output
css = """
<style>
body { font-family: Arial, sans-serif; font-size: 1.1em; margin: 1.5em; color: #111; }
h1, h2, h3, h4 { margin-top: 1.4em; margin-bottom: 0.4em; }
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #ccc; padding: 4px 8px; }
ul { margin-left: 1.5em; }
img { max-width: 100%; height: auto; }
figure { margin: 1em 0; }
figcaption { font-size: 0.95em; color: #555; }
a { color: #005ea2; text-decoration: underline; }
</style>
"""

# Utility Functions

def is_big_title(block, doc):
    """Determine if a text block should be treated as a main heading"""
    if block['type'] != 0 or len(block['lines']) == 0:
        return False
    
    try:
        # Compare block's max font size with document's max font size
        max_font = max(
            span['size']
            for line in block['lines']
            for span in line['spans']
            if 'size' in span
        )
        max_doc_font = max(
            span['size']
            for p in doc
            for b in p.get_text("dict")["blocks"] if b['type'] == 0
            for l in b['lines']
            for span in l['spans']
            if 'size' in span
        )
        return max_font >= max_doc_font - 0.1
    except (ValueError, KeyError):
        return False

def safe_ocr(pil_img):
    """Safely extract text from image using OCR"""
    if not tesseract_available:
        return "Image (OCR not available)"
    
    try:
        text = pytesseract.image_to_string(pil_img, lang="fra").strip()
        return text if text else "Image with no detectable text"
    except Exception as e:
        logger.warning(f"OCR error: {e}")
        return "Image (OCR error)"

def pdf_to_accessible_html(pdf_path: str):
    """Convert PDF file to accessible HTML format"""
    # Open PDF
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unable to open PDF: {str(e)}")
    
    try:
        # Extract title and initialize HTML
        title = doc.metadata.get('title', 'Document') or 'Document'
        html_output = [
            f'<html lang="fr"><head><meta charset="UTF-8"><title>{title} Accessible</title>{css}</head><body>',
            f"<h1>{title}</h1>"
        ]

        # Process each page
        for page_num, page in enumerate(doc, start=1):
            html_output.append(f"<section aria-label='Page {page_num}'>")
            
            try:
                # Extract and sort text blocks by position
                blocks = sorted(
                    page.get_text("dict")["blocks"], 
                    key=lambda b: (b.get("bbox", [0,0,0,0])[1], b.get("bbox", [0,0,0,0])[0])
                )
            except Exception as e:
                logger.warning(f"Error extracting blocks from page {page_num}: {e}")
                html_output.append(f"<p>Error processing page {page_num}</p>")
                html_output.append("</section>")
                continue

            # Extract hyperlinks
            links_zones = []
            try:
                links = page.get_links()
                for l in links:
                    if l['kind'] == 2 and 'uri' in l:
                        links_zones.append((l['from'], l['uri']))
            except Exception as e:
                logger.warning(f"Error extracting links: {e}")
                
            def find_link_for_span(span_bbox):
                """Check if text span overlaps with a hyperlink"""
                try:
                    for bbox, uri in links_zones:
                        x0, y0, x1, y1 = bbox
                        sx0, sy0, sx1, sy1 = span_bbox
                        cx, cy = (sx0+sx1)/2, (sy0+sy1)/2
                        if x0 <= cx <= x1 and y0 <= cy <= y1:
                            return uri
                except Exception:
                    pass
                return None

            # Process each block (text or image)
            for block in blocks:
                try:
                    if block["type"] == 0:  # Text block
                        # Extract and combine text from all spans
                        content = []
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "").strip()
                                if not text:
                                    continue
                                text = text.replace('\u2022', '').replace('\uf0b7', '')
                                
                                # Check for hyperlinks
                                link = find_link_for_span(span.get("bbox", [0,0,0,0]))
                                if link:
                                    text = f'<a href="{link}">{text}</a>'
                                else:
                                    # Auto-detect URLs in text
                                    url_match = re.search(r"(https?://[^\s]+|www\.[^\s]+)", text)
                                    if url_match:
                                        url = url_match.group(0)
                                        if not url.startswith("http"):
                                            url = "http://" + url
                                        text = re.sub(r"(https?://[^\s]+|www\.[^\s]+)", f'<a href="{url}">{url}</a>', text)
                                content.append(text)
                        
                        content_text = " ".join(content)
                        if not content_text:
                            continue
                            
                        # Handle bullet point lists
                        if '•' in content_text or '\uf0b7' in content_text:
                            items = [itm.strip(" ;:") for itm in re.split(r'[•\uf0b7]', content_text) if itm.strip()]
                            if len(items) > 1:
                                html_output.append("<ul>")
                                for itm in items:
                                    if itm.strip():
                                        html_output.append(f"<li>{itm}</li>")
                                html_output.append("</ul>")
                                continue

                        # Determine HTML tag based on font size
                        tag = "h2" if is_big_title(block, doc) else "p"
                        html_output.append(f"<{tag}>{content_text}</{tag}>")
                        
                    elif block["type"] == 1:  # Image block
                        raw = block.get("image")
                        if not raw:
                            continue
                            
                        try:
                            # Process image and embed as base64
                            pil_img = Image.open(BytesIO(raw))
                            buffer = BytesIO()
                            pil_img.save(buffer, format=pil_img.format or 'PNG')
                            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            mime = f"image/{(pil_img.format or 'png').lower()}"
                            alt = safe_ocr(pil_img)
                            
                            html_output.append(
                                "<figure>"
                                f"<img src='data:{mime};base64,{img_base64}' alt='{alt}'>"
                                f"<figcaption>{alt}</figcaption>"
                                "</figure>"
                            )
                        except Exception as e:
                            logger.warning(f"Error processing image: {e}")
                            html_output.append("<p>Image not processed (conversion error)</p>")
                            
                except Exception as e:
                    logger.warning(f"Error processing block: {e}")
                    continue

            html_output.append("</section>")
            
        html_output.append("</body></html>")
        return "\n".join(html_output), title
        
    finally:
        doc.close()

# API Endpoints

@app.get("/")
async def root():
    """Basic API information"""
    return {"message": "PDF to HTML Converter API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check with system diagnostics"""
    return {
        "status": "healthy",
        "tesseract_available": tesseract_available,
        "platform": platform.system()
    }

@app.post("/convert")
async def convert_pdf(file: UploadFile):
    """Convert PDF to accessible HTML with validation and scoring"""
    
    # Input validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    if not file.size or file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (maximum 50MB)")
    
    tmp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="File is empty")
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Convert PDF to HTML
        html_content, title = pdf_to_accessible_html(tmp_path)
        
        # Calculate accessibility score
        score = 100
        warnings = []
        
        if "alt=" not in html_content or "alt=''" in html_content:
            score -= 10
            warnings.append("Some images lack descriptions (alt text)")
            
        if "<table" in html_content and "role=" not in html_content:
            score -= 10
            warnings.append("Some tables lack accessibility attributes")
            
        # Check heading structure
        header_counts = {
            'h1': html_content.count('<h1>'),
            'h2': html_content.count('<h2>'),
            'h3': html_content.count('<h3>'),
        }
        
        if header_counts['h1'] == 0:
            score -= 5
            warnings.append("Document without main title (H1)")
        elif header_counts['h1'] > 1:
            score -= 3
            warnings.append("Multiple H1 titles")
        
        if not tesseract_available:
            warnings.append("OCR not available - limited image descriptions")
        
        return {
            "html": html_content,
            "title": title,
            "accessibilityScore": max(0, score),
            "warnings": warnings,
            "metadata": {
                "filename": file.filename,
                "size": file.size,
                "tesseract_used": tesseract_available
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        raise HTTPException(status_code=500, detail=f"Error during PDF conversion: {str(e)}")
    finally:
        # Clean up temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Unable to delete temporary file: {e}")

# Server Startup
if __name__ == "__main__":
    """Run the server directly - accessible at http://localhost:8000"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
