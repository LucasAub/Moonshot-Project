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
        # 1) Table extraction with Camelot
        tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
        if tables:
            for t in tables:
                df = t.df.copy()
                # First row as header
                df.columns = df.iloc[0]
                df = df.drop(0).reset_index(drop=True)
                html_output.append("<table role='table'>")
                html_output.append("<thead><tr>")
                for col in df.columns:
                    html_output.append(f"<th scope='col'>{col}</th>")
                html_output.append("</tr></thead><tbody>")
                
                for _, row in df.iterrows():
                    html_output.append("<tr>")
                    for cell in row:
                        html_output.append(f"<td>{cell}</td>")
                    html_output.append("</tr>")
                html_output.append("</tbody></table>")
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
                
                # Check for header level
                header_tag = analyze_title(block)
                tag = header_tag if header_tag else "p"
                html_output.append(f"<{tag}>{content}</{tag}>")
            
            elif block["type"] == 1:
                # Image processing
                raw = block.get("image")
                if not raw:
                    continue
                    
                pil_img = Image.open(BytesIO(raw))
                ext = 'jpg' if pil_img.format.lower() == 'jpeg' else pil_img.format.lower()
                img_fn = os.path.join(temp_dir, f"image_{page_num}_{uuid.uuid4().hex}.{ext}")
                pil_img.save(img_fn)
                
                alt = pytesseract.image_to_string(pil_img, lang="fra").strip() or "Image sans description détectable"
                html_output.append(
                    "<figure>"
                    f"<img src='data:image/{ext};base64,{raw}' alt='{alt}'>"  # Embed image as base64
                    f"<figcaption>{alt}</figcaption>"
                    "</figure>"
                )
                
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
        if "<h1" not in html_content:
            score -= 5
            warnings.append("Document may be missing a main heading")
            
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
