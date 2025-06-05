from fastapi import FastAPI, UploadFile, HTTPException
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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/' # Path to Tesseract data files
# if not os.path.exists(os.environ['TESSDATA_PREFIX']):
#     raise RuntimeError(f"Tesseract data directory not found: {os.environ['TESSDATA_PREFIX']}")

try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {tesseract_version}")
except Exception as e:
    logger.error(f"Tesseract initialization error: {e}")

app = FastAPI() # App init
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic CSS for HTML output to ensure readability and structure
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

def is_big_title(block, doc): # Detection of big titles
    if block['type'] != 0 or len(block['lines']) == 0:
        return False
    max_font = max(
        span['size']
        for line in block['lines']
        for span in line['spans']
    )
    max_doc_font = max(
        span['size']
        for p in doc
        for b in p.get_text("dict")["blocks"] if b['type'] == 0
        for l in b['lines']
        for span in l['spans']
    )
    return max_font >= max_doc_font - 0.1  # float tolerance

def pdf_to_accessible_html(pdf_path: str): # Convert PDF to accessible HTML
    doc = fitz.open(pdf_path)
    title = doc.metadata.get('title', 'Document') # Default title if not present
    html_output = [
        f'<html lang="fr"><head><meta charset="UTF-8"><title>{title} Accessible</title>{css}</head><body>',
        f"<h1>{title}</h1>"
    ]

    for page_num, page in enumerate(doc, start=1): # Iterate through each page
        html_output.append(f"<section aria-label='Page {page_num}'>") 
        blocks = sorted( # Sort blocks by vertical position and then horizontal
            page.get_text("dict")["blocks"], 
            key=lambda b: (b.get("bbox", [0,0,0,0])[1], b.get("bbox", [0,0,0,0])[0]) # Sort by y0, then x0
        )

        # Links extraction
        links = page.get_links()
        links_zones = []
        for l in links:
            if l['kind'] == 2 and 'uri' in l:
                links_zones.append((l['from'], l['uri'])) 
                
        def find_link_for_span(span_bbox): # Find link for a span
            for bbox, uri in links_zones:
                x0, y0, x1, y1 = bbox
                sx0, sy0, sx1, sy1 = span_bbox
                cx, cy = (sx0+sx1)/2, (sy0+sy1)/2
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    return uri
            return None

        for block in blocks: # Process each block
            if block["type"] == 0:
                content = []
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        text = text.replace('\u2022', '').replace('\uf0b7', '') 
                        link = find_link_for_span(span["bbox"])
                        if link:
                            text = f'<a href="{link}">{text}</a>'
                        # Check for links in the text
                        # If no link found, check for URLs and convert them to links
                        url_match = re.search(r"(https?://[^\s]+|www\.[^\s]+)", text)
                        if url_match and not link:
                            url = url_match.group(0)
                            if not url.startswith("http"):
                                url = "http://" + url
                            text = re.sub(
                                r"(https?://[^\s]+|www\.[^\s]+)",
                                f'<a href="{url}">{url}</a>',
                                text
                            )
                        content.append(text)
                content = " ".join(content)
                if not content:
                    continue
                if '' in content: # recognize bullet points
                    items = [itm.strip(" ;:") for itm in content.split('') if itm.strip()]
                    html_output.append("<ul>")
                    for itm in items:
                        html_output.append(f"<li>{itm}</li>")
                    html_output.append("</ul>")
                    continue

                tag = "h2" if is_big_title(block, doc) else "p"
                html_output.append(f"<{tag}>{content}</{tag}>")
            elif block["type"] == 1:
                raw = block.get("image")
                if not raw:
                    continue
                pil_img = Image.open(BytesIO(raw))
                # Embedding image in base64
                buffer = BytesIO()
                pil_img.save(buffer, format=pil_img.format)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                mime = f"image/{pil_img.format.lower()}"
                alt = pytesseract.image_to_string(pil_img, lang="fra").strip() or "Image sans texte détectable"
                html_output.append(
                    "<figure>"
                    f"<img src='data:{mime};base64,{img_base64}' alt='{alt}'>"
                    f"<figcaption>{alt}</figcaption>"
                    "</figure>"
                )

        html_output.append("</section>")
    html_output.append("</body></html>")
    doc.close()
    return "\n".join(html_output), title

@app.post("/convert")
async def convert_pdf(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name
    tmp.close()
    try:
        html_content, title = pdf_to_accessible_html(tmp_path)
        # Calculate accessibility score
        score = 100
        warnings = []
        if "alt=" not in html_content:
            score -= 10
            warnings.append("Certaines images n'ont pas de description (alt)")
        if "<table" in html_content and "role='table'" not in html_content:
            score -= 10
            warnings.append("Certains tableaux n'ont pas d'attribut d'accessibilité")
        header_counts = {
            'h1': html_content.count('<h1>'),
            'h2': html_content.count('<h2>'),
            'h3': html_content.count('<h3>'),
        }
        if header_counts['h1'] == 0:
            score -= 5
            warnings.append("Document sans titre principal (H1)")
        elif header_counts['h1'] > 1:
            score -= 3
            warnings.append("Plusieurs titres H1")
        return {
            "html": html_content,
            "title": title,
            "accessibilityScore": score,
            "warnings": warnings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
