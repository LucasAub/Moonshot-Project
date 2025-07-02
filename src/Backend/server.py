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
    border: 1px solid #ddd;
    background-color: #fff;
}
th, td { 
    border: 1px solid #ddd; 
    padding: 12px 16px; 
    text-align: left;
    vertical-align: top;
}
th {
    background-color: #f8f9fa;
    font-weight: 600;
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
}
tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}
tbody tr:hover {
    background-color: #e8f4f8;
    transition: background-color 0.2s ease;
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

def is_header_block(block: Dict[str, Any], doc, page_blocks: List[Dict]) -> tuple[bool, int]:
    """Enhanced header detection using multiple criteria."""
    if block['type'] != 0 or len(block['lines']) == 0:
        return False, 0
    
    try:
        # Get text content and properties
        text_content = ""
        max_font = 0
        is_bold = False
        
        for line in block["lines"]:
            for span in line["spans"]:
                text = span.get("text", "").strip()
                text_content += text + " "
                
                # Font size
                font_size = span.get('size', 0)
                if font_size > max_font:
                    max_font = font_size
                
                # Check if bold
                font_flags = span.get('flags', 0)
                if font_flags & 2**4:  # Bold flag
                    is_bold = True
        
        text_content = text_content.strip()
        
        # Skip if empty or too long for a header
        if not text_content or len(text_content) > 200:
            return False, 0
        
        # Calculate average font size in document
        all_font_sizes = []
        for p in doc:
            for b in p.get_text("dict")["blocks"]:
                if b['type'] == 0:
                    for l in b['lines']:
                        for span in l['spans']:
                            if 'size' in span:
                                all_font_sizes.append(span['size'])
        
        if not all_font_sizes:
            return False, 0
        
        avg_font_size = sum(all_font_sizes) / len(all_font_sizes)
        max_doc_font = max(all_font_sizes)
        
        # Header detection criteria
        header_score = 0
        
        # 1. Font size criteria (more flexible)
        if max_font >= avg_font_size * 1.2:  # 20% larger than average
            header_score += 2
        elif max_font >= avg_font_size * 1.1:  # 10% larger than average
            header_score += 1
        
        # 2. Bold text
        if is_bold:
            header_score += 2
        
        # 3. Position on page (blocks near top are more likely headers)
        block_y = block.get("bbox", [0, 0, 0, 0])[1]
        page_height = page_blocks[-1]["bbox"][3] if page_blocks else 1000
        relative_position = block_y / page_height if page_height > 0 else 0
        
        if relative_position < 0.3:  # Top 30% of page
            header_score += 1
        
        # 4. Text characteristics
        # Short text is more likely to be a header
        if len(text_content) < 50:
            header_score += 1
        
        # All caps might be a header
        if text_content.isupper() and len(text_content) > 3:
            header_score += 1
        
        # Ends with colon (like "Chapter 1:")
        if text_content.endswith(':'):
            header_score += 1
        
        # Contains numbers (like "1. Introduction")
        if re.match(r'^\d+\.?\s', text_content):
            header_score += 1
        
        # 5. Standalone block (not part of paragraph)
        if len(text_content.split()) <= 8:  # Short phrases
            header_score += 1
        
        # Determine header level based on font size and score
        if header_score >= 4:
            if max_font >= max_doc_font * 0.95:  # Very large font
                return True, 2  # h2
            else:
                return True, 3  # h3
        elif header_score >= 2 and max_font >= avg_font_size * 1.3:
            return True, 3  # h3
        
        return False, 0
        
    except (KeyError, ValueError) as e:
        logger.warning(f"Error in header detection: {e}")
        return False, 0

def detect_table_structure(blocks: List[Dict], start_idx: int) -> tuple[bool, List[List[str]], int]:
    """Detect and extract table structure from consecutive text blocks."""
    table_rows = []
    current_idx = start_idx
    
    # Look for table patterns in consecutive blocks
    for i in range(start_idx, min(start_idx + 20, len(blocks))):  # Check up to 20 blocks
        block = blocks[i]
        if block['type'] != 0:
            break
            
        # Extract text from block
        text_content = ""
        for line in block["lines"]:
            for span in line["spans"]:
                text_content += span.get("text", "").strip() + " "
        
        text_content = text_content.strip()
        if not text_content:
            break
        
        # Check for table-like patterns
        # Pattern 1: Tab-separated values
        if '\t' in text_content:
            cells = [cell.strip() for cell in text_content.split('\t') if cell.strip()]
            if len(cells) >= 2:
                table_rows.append(cells)
                current_idx = i + 1
                continue
        
        # Pattern 2: Multiple spaces (common in PDF tables)
        if re.search(r'\s{3,}', text_content):  # 3+ consecutive spaces
            # Split by multiple spaces
            cells = [cell.strip() for cell in re.split(r'\s{3,}', text_content) if cell.strip()]
            if len(cells) >= 2:
                table_rows.append(cells)
                current_idx = i + 1
                continue
        
        # Pattern 3: Pipe-separated values
        if '|' in text_content:
            cells = [cell.strip() for cell in text_content.split('|') if cell.strip()]
            if len(cells) >= 2:
                table_rows.append(cells)
                current_idx = i + 1
                continue
        
        # Pattern 4: Aligned columns (detect by position)
        bbox = block.get("bbox", [0, 0, 0, 0])
        # This is more complex - we'd need to analyze x-positions of text spans
        # For now, we'll use simpler patterns
        
        # If we haven't found a table pattern in this block, stop
        if not table_rows:
            break
        
        # If we found table rows but this block doesn't match, we might have reached the end
        break
    
    # Validate table structure
    if len(table_rows) >= 2:  # At least 2 rows
        # Check if rows have similar number of columns
        col_counts = [len(row) for row in table_rows]
        if max(col_counts) - min(col_counts) <= 1:  # Allow 1 column difference
            return True, table_rows, current_idx
    
    return False, [], start_idx

def process_text_block(block: Dict[str, Any], html_output: List[str], find_link_for_span, doc, page_blocks: List[Dict], block_index: int) -> int:
    """Enhanced text block processing with header and table detection."""
    
    # Check if this might be the start of a table
    is_table, table_rows, next_index = detect_table_structure(page_blocks, block_index)
    
    if is_table:
        # Process as table
        html_output.append('<table role="table">')
        
        # First row as header if it looks like one
        first_row = table_rows[0]
        remaining_rows = table_rows[1:]
        
        # Check if first row should be header (shorter text, different formatting)
        is_header_row = (
            len(first_row) == len(table_rows[1]) if len(table_rows) > 1 else False
        ) and all(len(cell) < 50 for cell in first_row)
        
        if is_header_row:
            html_output.append('<thead>')
            html_output.append('<tr>')
            for cell in first_row:
                html_output.append(f'<th scope="col">{cell}</th>')
            html_output.append('</tr>')
            html_output.append('</thead>')
            
            html_output.append('<tbody>')
            for row in remaining_rows:
                html_output.append('<tr>')
                for cell in row:
                    html_output.append(f'<td>{cell}</td>')
                html_output.append('</tr>')
            html_output.append('</tbody>')
        else:
            html_output.append('<tbody>')
            for row in table_rows:
                html_output.append('<tr>')
                for cell in row:
                    html_output.append(f'<td>{cell}</td>')
                html_output.append('</tr>')
            html_output.append('</tbody>')
        
        html_output.append('</table>')
        return next_index  # Skip the blocks that were part of the table
    
    # Regular text processing
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
        return block_index + 1
    
    # Handle bullet points
    if '•' in content_text:
        items = [item.strip() for item in content_text.split('•') if item.strip()]
        if len(items) > 1:
            html_output.append('<ul>')
            for item in items:
                if item:  # Skip empty items
                    html_output.append(f'<li>{item}</li>')
            html_output.append('</ul>')
            return block_index + 1
    
    # Enhanced header detection
    is_header, header_level = is_header_block(block, doc, page_blocks)
    
    if is_header:
        tag = f"h{header_level}"
        html_output.append(f'<{tag}>{content_text}</{tag}>')
    else:
        html_output.append(f'<p>{content_text}</p>')
    
    return block_index + 1

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
                block_index = 0
                while block_index < len(blocks):
                    block = blocks[block_index]
                    try:
                        if block["type"] == 0:  # Text block
                            block_index = process_text_block(
                                block, html_output, find_link_for_span, doc, blocks, block_index
                            )
                        elif block["type"] == 1:  # Image block
                            process_image_block(block, html_output)
                            block_index += 1
                        else:
                            block_index += 1
                    except Exception as e:
                        logger.warning(f"Error processing block on page {page_num}: {e}")
                        block_index += 1
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

@app.get("/debug/features")
async def debug_features():
    """Debug endpoint to test header and table detection features."""
    return {
        "features": {
            "enhanced_header_detection": "Uses font size, bold text, position, and content analysis",
            "table_detection": "Detects tab-separated, space-separated, and pipe-separated tables",
            "criteria": {
                "headers": [
                    "Font size 20% larger than average",
                    "Bold text formatting",
                    "Position in top 30% of page",
                    "Short text (< 50 chars)",
                    "Uppercase text",
                    "Ends with colon",
                    "Starts with numbers (1., 2., etc.)",
                    "Standalone phrases (≤ 8 words)"
                ],
                "tables": [
                    "Tab-separated values (\\t)",
                    "Multiple spaces (3+ consecutive)",
                    "Pipe-separated values (|)",
                    "Minimum 2 rows, 2 columns",
                    "Similar column counts across rows"
                ]
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
