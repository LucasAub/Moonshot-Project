import pytest
import tempfile
import os
from PIL import Image
import io
import base64
from server_enhanced import is_big_title, safe_ocr, app
from fastapi.testclient import TestClient
import fitz

# Test client for the API
client = TestClient(app)

def test_health_endpoint():
    """Test that the /health endpoint works"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "tesseract_available" in data
    assert "platform" in data

def test_root_endpoint():
    """Test that the root endpoint works"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data

def test_is_big_title_function():
    """Test the big title detection function"""
    # Create a mock block with a large font
    mock_block = {
        'type': 0,
        'lines': [{
            'spans': [{'size': 20, 'text': 'Big Title'}]
        }]
    }
    
    # Create a mock document with a smaller font
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
    
    # The title should be detected as big
    result = is_big_title(mock_block, mock_doc)
    assert result == True

    # Test with an image block (type 1)
    mock_image_block = {'type': 1, 'lines': []}
    result = is_big_title(mock_image_block, mock_doc)
    assert result == False

def test_safe_ocr_function():
    """Test the safe OCR function"""
    # Create a simple image in memory
    img = Image.new('RGB', (100, 50), color='white')
    
    # Test the OCR function
    result = safe_ocr(img)
    
    # The result should be a string
    assert isinstance(result, str)
    
    # The result should not be empty
    assert len(result) > 0
    
    # It should contain either detected text or a status message
    assert any(msg in result for msg in [
        "Image", "OCR", "text", "not available", "error"
    ])

def test_convert_endpoint_no_file():
    """Test the conversion endpoint without a file"""
    response = client.post("/convert")
    assert response.status_code == 422  # Unprocessable Entity

def test_convert_endpoint_wrong_file_type():
    """Test the conversion endpoint with wrong file type"""
    # Create a text file instead of a PDF
    fake_file = io.BytesIO(b"This is not a PDF")
    
    response = client.post(
        "/convert",
        files={"file": ("test.txt", fake_file, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "PDF" in data["detail"]

def test_convert_endpoint_empty_file():
    """Test the conversion endpoint with an empty file"""
    fake_file = io.BytesIO(b"")
    
    response = client.post(
        "/convert",
        files={"file": ("empty.pdf", fake_file, "application/pdf")}
    )
    
    assert response.status_code == 400

def create_simple_pdf():
    """Create a simple PDF for testing"""
    # Create a simple PDF with PyMuPDF
    doc = fitz.open()  # New document
    page = doc.new_page()  # New page
    
    # Add text
    page.insert_text((50, 100), "Test Title", fontsize=20)
    page.insert_text((50, 150), "This is a test paragraph with normal text.", fontsize=12)
    
    # Save to memory
    pdf_bytes = doc.write()
    doc.close()
    
    return io.BytesIO(pdf_bytes)

def test_convert_endpoint_valid_pdf():
    """Test the conversion endpoint with a valid PDF"""
    pdf_file = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", pdf_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check the response structure
    assert "html" in data
    assert "title" in data
    assert "accessibilityScore" in data
    assert "warnings" in data
    assert "metadata" in data
    
    # Check that the HTML contains expected elements
    html = data["html"]
    assert "<html" in html
    assert "<h1>" in html
    assert "<h2>" in html or "<p>" in html  # At least one of these tags
    assert "</html>" in html
    
    # Check metadata
    metadata = data["metadata"]
    assert "filename" in metadata
    assert "size" in metadata
    assert "tesseract_used" in metadata

def test_html_tags_conversion():
    """Specific test to check that HTML tags are properly generated"""
    pdf_file = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test_tags.pdf", pdf_file, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    html = data["html"]
    
    # Check the presence of essential tags
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
    
    # Check that CSS is included
    assert "<style>" in html
    assert "font-family:" in html

def test_image_processing():
    """Test to check image processing in PDF"""
    # Create a PDF with an image
    doc = fitz.open()
    page = doc.new_page()
    
    # Create a simple image
    img = Image.new('RGB', (100, 50), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Insert the image in the PDF
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
    
    # Check that the image is properly processed
    assert "<figure>" in html
    assert "<img" in html
    assert "alt=" in html
    assert "<figcaption>" in html
    assert "data:image/" in html  # Base64 encoded image

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
