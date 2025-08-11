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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Tesseract pour Windows
if platform.system() == "Windows":
    # Essayer de trouver Tesseract dans les emplacements communs sur Windows
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
            logger.info(f"Tesseract trouvé à: {path}")
            break
    
    if not tesseract_found:
        logger.warning("Tesseract non trouvé. L'OCR sera désactivé.")
else:
    # Configuration pour macOS/Linux
    os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata/'

# Test de Tesseract
tesseract_available = False
try:
    tesseract_version = pytesseract.get_tesseract_version()
    logger.info(f"Tesseract version: {tesseract_version}")
    tesseract_available = True
except Exception as e:
    logger.warning(f"Tesseract non disponible: {e}")
    tesseract_available = False

app = FastAPI(title="PDF to HTML Converter", version="1.0.0")

# Gestionnaire d'erreurs global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erreur interne du serveur",
            "error": str(exc),
            "type": "internal_server_error"
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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

def is_big_title(block, doc):
    """Detection of big titles"""
    if block['type'] != 0 or len(block['lines']) == 0:
        return False
    
    try:
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
    """Effectue l'OCR de manière sécurisée"""
    if not tesseract_available:
        return "Image (OCR non disponible)"
    
    try:
        text = pytesseract.image_to_string(pil_img, lang="fra").strip()
        return text if text else "Image sans texte détectable"
    except Exception as e:
        logger.warning(f"Erreur OCR: {e}")
        return "Image (erreur OCR)"

def pdf_to_accessible_html(pdf_path: str):
    """Convert PDF to accessible HTML"""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impossible d'ouvrir le PDF: {str(e)}")
    
    try:
        title = doc.metadata.get('title', 'Document') or 'Document'
        html_output = [
            f'<html lang="fr"><head><meta charset="UTF-8"><title>{title} Accessible</title>{css}</head><body>',
            f"<h1>{title}</h1>"
        ]

        for page_num, page in enumerate(doc, start=1):
            html_output.append(f"<section aria-label='Page {page_num}'>")
            
            try:
                blocks = sorted(
                    page.get_text("dict")["blocks"], 
                    key=lambda b: (b.get("bbox", [0,0,0,0])[1], b.get("bbox", [0,0,0,0])[0])
                )
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction des blocs de la page {page_num}: {e}")
                html_output.append(f"<p>Erreur lors du traitement de la page {page_num}</p>")
                html_output.append("</section>")
                continue

            # Links extraction
            links = []
            links_zones = []
            try:
                links = page.get_links()
                for l in links:
                    if l['kind'] == 2 and 'uri' in l:
                        links_zones.append((l['from'], l['uri']))
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction des liens: {e}")
                
            def find_link_for_span(span_bbox):
                """Find link for a span"""
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

            for block in blocks:
                try:
                    if block["type"] == 0:  # Text block
                        content = []
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "").strip()
                                if not text:
                                    continue
                                text = text.replace('\u2022', '').replace('\uf0b7', '')
                                
                                # Vérifier les liens
                                link = find_link_for_span(span.get("bbox", [0,0,0,0]))
                                if link:
                                    text = f'<a href="{link}">{text}</a>'
                                else:
                                    # Chercher des URLs dans le texte
                                    url_match = re.search(r"(https?://[^\s]+|www\.[^\s]+)", text)
                                    if url_match:
                                        url = url_match.group(0)
                                        if not url.startswith("http"):
                                            url = "http://" + url
                                        text = re.sub(
                                            r"(https?://[^\s]+|www\.[^\s]+)",
                                            f'<a href="{url}">{url}</a>',
                                            text
                                        )
                                content.append(text)
                        
                        content_text = " ".join(content)
                        if not content_text:
                            continue
                            
                        # Traitement des listes à puces
                        if '•' in content_text or '\uf0b7' in content_text:
                            items = [itm.strip(" ;:") for itm in re.split(r'[•\uf0b7]', content_text) if itm.strip()]
                            if len(items) > 1:
                                html_output.append("<ul>")
                                for itm in items:
                                    if itm.strip():
                                        html_output.append(f"<li>{itm}</li>")
                                html_output.append("</ul>")
                                continue

                        tag = "h2" if is_big_title(block, doc) else "p"
                        html_output.append(f"<{tag}>{content_text}</{tag}>")
                        
                    elif block["type"] == 1:  # Image block
                        raw = block.get("image")
                        if not raw:
                            continue
                            
                        try:
                            pil_img = Image.open(BytesIO(raw))
                            # Embedding image in base64
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
                            logger.warning(f"Erreur lors du traitement de l'image: {e}")
                            html_output.append("<p>Image non traitée (erreur de conversion)</p>")
                            
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement d'un bloc: {e}")
                    continue

            html_output.append("</section>")
            
        html_output.append("</body></html>")
        return "\n".join(html_output), title
        
    finally:
        doc.close()

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {"message": "PDF to HTML Converter API", "status": "running"}

@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "tesseract_available": tesseract_available,
        "platform": platform.system()
    }

@app.post("/convert")
async def convert_pdf(file: UploadFile):
    """Convertit un PDF en HTML accessible"""
    
    # Validation du fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    if not file.size or file.size == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide")
    
    # Limite de taille (50MB)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Le fichier est trop volumineux (maximum 50MB)")
    
    tmp_path = None
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Le fichier est vide")
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Conversion
        html_content, title = pdf_to_accessible_html(tmp_path)
        
        # Calcul du score d'accessibilité
        score = 100
        warnings = []
        
        # Vérifications d'accessibilité
        if "alt=" not in html_content or "alt=''" in html_content:
            score -= 10
            warnings.append("Certaines images n'ont pas de description (alt)")
            
        if "<table" in html_content and "role=" not in html_content:
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
        
        if not tesseract_available:
            warnings.append("OCR non disponible - descriptions d'images limitées")
        
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
        logger.error(f"Erreur lors de la conversion: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la conversion du PDF: {str(e)}"
        )
    finally:
        # Nettoyage du fichier temporaire
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
