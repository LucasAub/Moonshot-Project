from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import uuid
import re
from io import BytesIO
import camelot
import tempfile
import os
import shutil
from pathlib import Path
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Tesseract environment variable to find language data
os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'

# Verify Tesseract configuration
try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {tesseract_version}")
    
    # Test if OCR works with a simple image (optional)
    # from PIL import Image, ImageDraw, ImageFont
    # test_img = Image.new('RGB', (100, 30), color=(255, 255, 255))
    # d = ImageDraw.Draw(test_img)
    # d.text((10, 10), "Test OCR", fill=(0, 0, 0))
    # test_result = pytesseract.image_to_string(test_img)
    # logger.info(f"OCR test result: {test_result}")
    
except Exception as e:
    logger.error(f"Tesseract initialization error: {e}")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def convert_pdf_to_html(pdf_path: str) -> tuple[str, str]:
    doc = fitz.open(pdf_path)
    
    # HTML header
    title = fitz.Document(pdf_path).metadata.get('title', 'Document')
    html_output = [
        f'<html lang="fr"><head><meta charset="UTF-8"><title>{title} Accessible</title></head><body>'
    ]

    # Collect all font sizes in the document to establish a hierarchy
    all_font_sizes = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block['type'] == 0:  # Text block
                for line in block['lines']:
                    for span in line['spans']:
                        if span['text'].strip():
                            all_font_sizes.append({
                                'size': span['size'], 
                                'flags': span['flags'],
                                'text': span['text']
                            })
    
    # Sort font sizes in descending order
    all_font_sizes.sort(key=lambda x: x['size'], reverse=True)
    
    # Get unique font sizes
    unique_sizes = sorted(list({f['size'] for f in all_font_sizes}), reverse=True)
    
    # Function to determine header level based on font size
    def get_header_level(font_size, is_bold=False):
        if len(unique_sizes) <= 1:
            return None  # No variation in font size, can't determine headers
            
        # If the font is significantly larger than average or is bold
        size_index = unique_sizes.index(font_size) if font_size in unique_sizes else -1
        
        # If it's one of the top 3 largest fonts or it's bold and in the top 5
        if size_index == 0:
            return 'h1'
        elif size_index == 1:
            return 'h2'
        elif size_index == 2 or (is_bold and size_index < 5):
            return 'h3'
        elif is_bold:
            return 'h4'
        return None
    
    # Function to know if a block is a title and what level
    def analyze_title(block):
        if block['type'] != 0 or len(block['lines']) == 0:
            return None
        
        # Get max font size and check if any span is bold
        max_font = max(
            span['size']
            for line in block['lines']
            for span in line['spans']
        )
        
        # Check if any text is bold (flag 4 indicates bold)
        has_bold = any(
            span['flags'] & 4
            for line in block['lines']
            for span in line['spans']
        )
        
        # Get the text content
        content = " ".join(
            span['text'].strip()
            for line in block['lines']
            for span in line['spans']
            if span['text'].strip()
        )
        
        # Short text is more likely to be a header
        is_short_text = len(content.split()) <= 10
        
        # Additional heuristics: all caps may indicate headers
        is_all_caps = content.isupper()
        
        # Get header level based on font size
        header_level = get_header_level(max_font, has_bold)
        
        # Apply additional rules
        if is_all_caps and is_short_text and not header_level:
            header_level = 'h3'
        elif is_short_text and has_bold and not header_level:
            header_level = 'h4'
        
        return header_level

    # Create a temporary directory for images
    temp_dir = tempfile.mkdtemp()
    
    for page_num, page in enumerate(doc, start=1):
        html_output.append(f"<section aria-label='Page {page_num}'>")
        # 1) Table extraction with Camelot - try both lattice and stream flavors
        tables = []
        try:
            # Try lattice flavor first (for tables with visible borders)
            lattice_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
            if lattice_tables and len(lattice_tables) > 0:
                tables = lattice_tables
            else:
                # If no tables found with lattice, try stream flavor (for tables without visible borders)
                stream_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='stream')
                if stream_tables and len(stream_tables) > 0:
                    tables = stream_tables
        except Exception as table_error:
            logger.warning(f"Table extraction error on page {page_num}: {table_error}")
        
        if tables and len(tables) > 0:
            for t in tables:
                try:
                    df = t.df.copy()
                    if df.empty:
                        continue
                        
                    # First row as header, but only if it looks like a header
                    has_header = True
                    if len(df) > 1:  # Check if we have more than one row
                        # If first row has mostly empty cells, it's probably not a header
                        empty_cells_ratio = df.iloc[0].isna().sum() / len(df.columns)
                        if empty_cells_ratio > 0.5:  # If more than 50% of cells are empty
                            has_header = False
                    
                    if has_header:
                        # Replace NaN with empty string in the header row
                        df.iloc[0] = df.iloc[0].fillna('')
                        df.columns = df.iloc[0]
                        df = df.drop(0).reset_index(drop=True)
                    
                    # Replace NaN with empty string in the entire dataframe
                    df = df.fillna('')
                    
                    html_output.append("<div class='table-responsive'>")
                    html_output.append("<table role='table' class='table table-bordered'>")
                    
                    # Add column headers
                    html_output.append("<thead><tr>")
                    for col in df.columns:
                        html_output.append(f"<th scope='col'>{col}</th>")
                    html_output.append("</tr></thead><tbody>")
                    
                    # Add table rows
                    for _, row in df.iterrows():
                        html_output.append("<tr>")
                        for cell in row:
                            html_output.append(f"<td>{cell}</td>")
                        html_output.append("</tr>")
                    html_output.append("</tbody></table>")
                    html_output.append("</div>")
                except Exception as df_error:
                    logger.error(f"Error processing table: {df_error}")
                    html_output.append("<p>[Table non traitée]</p>")
            
            html_output.append("</section>")
            continue

        # 2) If there are no tables, extract the text
        blocks = sorted(
            page.get_text("dict")["blocks"],
            key=lambda b: (b.get("bbox", [0,0,0,0])[1], b.get("bbox", [0,0,0,0])[0])
        )
        for block in blocks:
            if block["type"] == 0:
                # Text processing
                raw_lines = []
                for line in block["lines"]:
                    spans = [
                        (span["bbox"][0], span["text"])
                        for span in line["spans"]
                        if span["text"].strip()
                    ]
                    if spans:
                        raw_lines.append(spans)
                
                content = " ".join(
                    span["text"].strip()
                    for line in block["lines"]
                    for span in line["spans"]
                    if span["text"].strip()
                )
                
                if not content:
                    continue
                
                # Check for bullet points and replace with standard bullet
                content = content.replace('\u2022', '•').replace('\uf0b7', '•')
                
                # Handle bullet point lists
                if '•' in content:
                    items = [itm.strip(' ;:') for itm in content.split('•') if itm.strip()]
                    html_output.append("<ul>")
                    for itm in items:
                        html_output.append(f"<li>{itm}</li>")
                    html_output.append("</ul>")
                    continue
                
                # Handle numbered lists (e.g., "1. Item", "2. Item")
                if re.match(r'^\d+[\.\)]\s+\w+', content):
                    # Split on newlines and check if most lines start with a number
                    lines = content.split('\n')
                    numbered_lines = [l for l in lines if re.match(r'^\d+[\.\)]\s+\w+', l)]
                    
                    if len(numbered_lines) > 0 and len(numbered_lines) >= len(lines) * 0.5:  # At least half the lines are numbered
                        html_output.append("<ol>")
                        for line in lines:
                            # Remove the number and punctuation from the start of the line
                            clean_item = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                            if clean_item:
                                html_output.append(f"<li>{clean_item}</li>")
                        html_output.append("</ol>")
                        continue
                
                # Handle URLs - convert them to clickable links
                url_pattern = r'https?://[^\s<>")]+|www\.[^\s<>")]+\.[^\s<>")]+(?=[\s<>]|$)'
                content = re.sub(url_pattern, lambda m: f'<a href="{m.group(0)}" target="_blank">{m.group(0)}</a>', content)
                
                # Check for header level
                header_tag = analyze_title(block)
                tag = header_tag if header_tag else "p"
                html_output.append(f"<{tag}>{content}</{tag}>")
            
            elif block["type"] == 1:
                # Image processing
                raw = block.get("image")
                if not raw:
                    continue
                
                try:
                    # Open image using PIL
                    pil_img = Image.open(BytesIO(raw))
                    ext = 'jpg' if pil_img.format and pil_img.format.lower() == 'jpeg' else (pil_img.format.lower() if pil_img.format else 'png')
                    
                    # Save image temporarily for processing
                    img_fn = os.path.join(temp_dir, f"image_{page_num}_{uuid.uuid4().hex}.{ext}")
                    pil_img.save(img_fn)
                    
                    # Generate alt text using OCR
                    try:
                        # Try to enhance the image for better OCR
                        ocr_img = pil_img.copy()
                        
                        # Convert to grayscale and increase contrast if it's not a small icon
                        if ocr_img.width > 50 and ocr_img.height > 50:
                            from PIL import ImageEnhance
                            ocr_img = ocr_img.convert('L')  # Convert to grayscale
                            enhancer = ImageEnhance.Contrast(ocr_img)
                            ocr_img = enhancer.enhance(1.5)  # Increase contrast
                        
                        # Attempt OCR with French language
                        alt = pytesseract.image_to_string(ocr_img, lang="fra").strip()
                        
                        # If French OCR fails or returns little text, try English
                        if not alt or len(alt) < 3:
                            alt_en = pytesseract.image_to_string(ocr_img, lang="eng").strip()
                            if len(alt_en) > len(alt):
                                alt = alt_en
                        
                        # If still no text, provide a generic description
                        if not alt:
                            # Provide description based on image size
                            if pil_img.width < 100 and pil_img.height < 100:
                                alt = "Icône ou petit graphique"
                            elif pil_img.width > 500 or pil_img.height > 500:
                                alt = "Image grande taille - potentiellement un diagramme ou une photo"
                            else:
                                alt = "Image sans texte détectable"
                    except Exception as e:
                        logger.warning(f"Tesseract OCR error: {e}")
                        alt = "Image sans description textuelle (OCR échec)"
                    
                    # Clean up alt text - remove excessive whitespace and line breaks
                    alt = re.sub(r'\s+', ' ', alt).strip()
                    
                    # Limit alt text length for readability
                    if len(alt) > 250:
                        alt = alt[:247] + "..."
                    
                    # Convert raw image data to base64 for embedding
                    img_base64 = base64.b64encode(raw).decode('utf-8')
                    
                    html_output.append(
                        "<figure>"
                        f"<img src='data:image/{ext};base64,{img_base64}' alt='{alt}'>"
                        f"<figcaption>{alt}</figcaption>"
                        "</figure>"
                    )
                except Exception as img_error:
                    logger.error(f"Image processing error: {img_error}")
                    html_output.append("<p>[Image non traitée]</p>")
                
        html_output.append("</section>")

    # Check if document has an h1 heading - if not, use the title as h1
    if "<h1>" not in "".join(html_output):
        # Insert h1 at the beginning of the body
        document_title = title if title and title != "Document" else "Document"
        html_output.insert(1, f"<h1>{document_title}</h1>")
    
    html_output.append("</body></html>")
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    
    return "\n".join(html_output), title

@app.post("/convert")
async def convert_pdf(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        html_content, title = convert_pdf_to_html(tmp_path)
        
        # Calculate a simple accessibility score (can be enhanced)
        score = 100
        warnings = []
        
        # Check for common accessibility features
        if "alt=" not in html_content:
            score -= 10
            warnings.append("Some images may be missing alt text")
        if "<table" in html_content and "role='table'" not in html_content:
            score -= 10
            warnings.append("Tables may not be properly marked for accessibility")
        
        # Check header structure
        header_counts = {
            'h1': html_content.count('<h1>'),
            'h2': html_content.count('<h2>'),
            'h3': html_content.count('<h3>'),
            'h4': html_content.count('<h4>'),
            'h5': html_content.count('<h5>'),
            'h6': html_content.count('<h6>')
        }
        
        # Document should have exactly one h1
        if header_counts['h1'] == 0:
            score -= 5
            warnings.append("Document is missing a main heading (H1)")
        elif header_counts['h1'] > 1:
            score -= 3
            warnings.append("Document has multiple main headings (H1), which is not recommended")
            
        # Check for proper header structure (h1 > h2 > h3...)
        if header_counts['h3'] > 0 and header_counts['h2'] == 0:
            score -= 3
            warnings.append("Document has H3 headers without H2 headers, suggesting improper structure")
        if header_counts['h4'] > 0 and header_counts['h3'] == 0:
            score -= 2
            warnings.append("Document has H4 headers without H3 headers, suggesting improper structure")
            
        return {
            "html": html_content,
            "title": title,
            "accessibilityScore": score,
            "warnings": warnings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
