import pytest
import tempfile
import os
from PIL import Image
import io
import base64
from server_enhanced import is_big_title, safe_ocr, app
from fastapi.testclient import TestClient
import fitz

# Client de test pour l'API
client = TestClient(app)

def test_health_endpoint():
    """Test que l'endpoint /health fonctionne"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "tesseract_available" in data
    assert "platform" in data

def test_root_endpoint():
    """Test que l'endpoint racine fonctionne"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data

def test_is_big_title_function():
    """Test la fonction de détection des gros titres"""
    # Créer un faux bloc avec une grande police
    mock_block = {
        'type': 0,
        'lines': [{
            'spans': [{'size': 20, 'text': 'Big Title'}]
        }]
    }
    
    # Créer un faux document avec une police plus petite
    mock_doc = [
        type('MockPage', (), {
            'get_text': lambda self, format: {
                'blocks': [{
                    'type': 0,
                    'lines': [{'spans': [{'size': 12}]}]
                }]
            }
        })()
    ]
    
    # Le titre devrait être détecté comme grand
    result = is_big_title(mock_block, mock_doc)
    assert result == True

    # Test avec un bloc d'image (type 1)
    mock_image_block = {'type': 1, 'lines': []}
    result = is_big_title(mock_image_block, mock_doc)
    assert result == False

def test_safe_ocr_function():
    """Test la fonction OCR sécurisée"""
    # Créer une image simple en mémoire
    img = Image.new('RGB', (100, 50), color='white')
    
    # Test de la fonction OCR
    result = safe_ocr(img)
    
    # Le résultat devrait être une chaîne
    assert isinstance(result, str)
    
    # Le résultat ne devrait pas être vide
    assert len(result) > 0
    
    # Il devrait contenir soit du texte détecté, soit un message d'état
    assert any(msg in result for msg in [
        "Image", "OCR", "texte", "non disponible", "erreur"
    ])

def test_convert_endpoint_no_file():
    """Test l'endpoint de conversion sans fichier"""
    response = client.post("/convert")
    assert response.status_code == 422  # Unprocessable Entity

def test_convert_endpoint_wrong_file_type():
    """Test l'endpoint de conversion avec un mauvais type de fichier"""
    # Créer un fichier texte au lieu d'un PDF
    fake_file = io.BytesIO(b"This is not a PDF")
    
    response = client.post(
        "/convert",
        files={"file": ("test.txt", fake_file, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "PDF" in data["detail"]

def test_convert_endpoint_empty_file():
    """Test l'endpoint de conversion avec un fichier vide"""
    fake_file = io.BytesIO(b"")
    
    response = client.post(
        "/convert",
        files={"file": ("empty.pdf", fake_file, "application/pdf")}
    )
    
    assert response.status_code == 400

def create_simple_pdf():
    """Créer un PDF simple pour les tests"""
    # Créer un PDF simple avec PyMuPDF
    doc = fitz.open()  # Nouveau document
    page = doc.new_page()  # Nouvelle page
    
    # Ajouter du texte
    page.insert_text((50, 100), "Test Title", fontsize=20)
    page.insert_text((50, 150), "This is a test paragraph with normal text.", fontsize=12)
    
    # Sauvegarder en mémoire
    pdf_bytes = doc.write()
    doc.close()
    
    return io.BytesIO(pdf_bytes)

def test_convert_endpoint_valid_pdf():
    """Test l'endpoint de conversion avec un PDF valide"""
    pdf_file = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", pdf_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Vérifier la structure de la réponse
    assert "html" in data
    assert "title" in data
    assert "accessibilityScore" in data
    assert "warnings" in data
    assert "metadata" in data
    
    # Vérifier que le HTML contient les éléments attendus
    html = data["html"]
    assert "<html" in html
    assert "<h1>" in html
    assert "<h2>" in html or "<p>" in html  # Au moins un de ces tags
    assert "</html>" in html
    
    # Vérifier les métadonnées
    metadata = data["metadata"]
    assert "filename" in metadata
    assert "size" in metadata
    assert "tesseract_used" in metadata

def test_html_tags_conversion():
    """Test spécifique pour vérifier que les tags HTML sont bien générés"""
    pdf_file = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test_tags.pdf", pdf_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    html = data["html"]
    
    # Vérifier la présence des tags essentiels
    assert "<html lang=\"fr\">" in html
    assert "<head>" in html
    assert "<meta charset=\"UTF-8\">" in html
    assert "<title>" in html
    assert "<body>" in html
    assert "<h1>" in html
    assert "<section aria-label=" in html
    assert "</section>" in html
    assert "</body>" in html
    assert "</html>" in html
    
    # Vérifier que le CSS est inclus
    assert "<style>" in html
    assert "font-family:" in html

def test_image_processing():
    """Test pour vérifier le traitement des images dans le PDF"""
    # Créer un PDF avec une image
    doc = fitz.open()
    page = doc.new_page()
    
    # Créer une image simple
    img = Image.new('RGB', (100, 50), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Insérer l'image dans le PDF
    img_rect = fitz.Rect(50, 50, 150, 100)
    page.insert_image(img_rect, stream=img_bytes.getvalue())
    
    pdf_bytes = doc.write()
    doc.close()
    
    pdf_file = io.BytesIO(pdf_bytes)
    
    response = client.post(
        "/convert",
        files={"file": ("test_image.pdf", pdf_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    html = data["html"]
    
    # Vérifier que l'image est bien traitée
    assert "<figure>" in html
    assert "<img" in html
    assert "alt=" in html
    assert "<figcaption>" in html
    assert "data:image/" in html  # Image encodée en base64

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
