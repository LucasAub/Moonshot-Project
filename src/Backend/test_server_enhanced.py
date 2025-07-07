import pytest
import tempfile
import os
import base64
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from PIL import Image
import fitz

# Import the module under test
from server_enhanced import (
    app,
    validate_file,
    safe_ocr_extract,
    calculate_accessibility_score,
    is_big_title,
    process_text_block,
    process_image_block,
    pdf_to_accessible_html,
    configure_tesseract,
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS
)

# Test client
client = TestClient(app)


class TestConfigureTesseract:
    """Test the configure_tesseract function."""
    
    @patch('server_enhanced.platform.system')
    @patch('server_enhanced.os.path.exists')
    @patch('server_enhanced.os.getenv')
    def test_configure_tesseract_windows_found(self, mock_getenv, mock_exists, mock_platform):
        """Test Tesseract configuration on Windows when found."""
        mock_platform.return_value = "Windows"
        mock_getenv.return_value = "TestUser"
        mock_exists.side_effect = lambda path: "Program Files\\Tesseract-OCR" in path
        
        with patch('server_enhanced.pytesseract.pytesseract') as mock_pytesseract:
            configure_tesseract()
            assert mock_pytesseract.tesseract_cmd is not None
    
    @patch('server_enhanced.platform.system')
    @patch('server_enhanced.os.path.exists')
    def test_configure_tesseract_windows_not_found(self, mock_exists, mock_platform):
        """Test Tesseract configuration on Windows when not found."""
        mock_platform.return_value = "Windows"
        mock_exists.return_value = False
        
        with patch('server_enhanced.logger') as mock_logger:
            configure_tesseract()
            mock_logger.warning.assert_called()
    
    @patch('server_enhanced.platform.system')
    @patch('server_enhanced.os.path.exists')
    def test_configure_tesseract_macos(self, mock_exists, mock_platform):
        """Test Tesseract configuration on macOS."""
        mock_platform.return_value = "Darwin"
        mock_exists.return_value = True
        
        with patch('server_enhanced.os.environ') as mock_environ:
            configure_tesseract()
            assert 'TESSDATA_PREFIX' in mock_environ or mock_environ.__setitem__.called
    
    @patch('server_enhanced.platform.system')
    def test_configure_tesseract_linux(self, mock_platform):
        """Test Tesseract configuration on Linux."""
        mock_platform.return_value = "Linux"
        # Should not raise any exceptions
        configure_tesseract()


class TestValidateFile:
    """Test the validate_file function."""
    
    def test_validate_file_no_filename(self):
        """Test validation with no filename."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        
        with pytest.raises(Exception) as exc_info:
            validate_file(mock_file)
        assert "No file provided" in str(exc_info.value)
    
    def test_validate_file_invalid_extension(self):
        """Test validation with invalid file extension."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        
        with pytest.raises(Exception) as exc_info:
            validate_file(mock_file)
        assert "Invalid file type" in str(exc_info.value)
    
    def test_validate_file_valid_pdf(self):
        """Test validation with valid PDF file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        
        # Should not raise any exception
        validate_file(mock_file)
    
    def test_validate_file_case_insensitive(self):
        """Test validation is case insensitive."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.PDF"
        
        # Should not raise any exception
        validate_file(mock_file)


class TestSafeOcrExtract:
    """Test the safe_ocr_extract function."""
    
    @patch('server_enhanced.pytesseract.image_to_string')
    def test_safe_ocr_extract_success(self, mock_ocr):
        """Test successful OCR extraction."""
        mock_ocr.return_value = "  Extracted text  "
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image)
        assert result == "Extracted text"
        mock_ocr.assert_called_once_with(mock_image, lang="eng")
    
    @patch('server_enhanced.pytesseract.image_to_string')
    def test_safe_ocr_extract_empty_result(self, mock_ocr):
        """Test OCR extraction with empty result."""
        mock_ocr.return_value = "   "
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image)
        assert result == "Image sans texte détectable"
    
    @patch('server_enhanced.pytesseract.image_to_string')
    @patch('server_enhanced.logger')
    def test_safe_ocr_extract_exception(self, mock_logger, mock_ocr):
        """Test OCR extraction with exception."""
        mock_ocr.side_effect = Exception("OCR failed")
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image)
        assert result == "Image sans texte détectable"
        mock_logger.warning.assert_called()
    
    @patch('server_enhanced.pytesseract.image_to_string')
    def test_safe_ocr_extract_custom_language(self, mock_ocr):
        """Test OCR extraction with custom language."""
        mock_ocr.return_value = "Texte français"
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image, lang="fra")
        assert result == "Texte français"
        mock_ocr.assert_called_once_with(mock_image, lang="fra")


class TestCalculateAccessibilityScore:
    """Test the calculate_accessibility_score function."""
    
    def test_perfect_accessibility_score(self):
        """Test perfect accessibility score."""
        html_content = """
        <h1>Main Title</h1>
        <h2>Subtitle</h2>
        <p>Some content</p>
        <img src="test.jpg" alt="Test image">
        <table role="table" aria-label="Test table">
            <tr><th>Header</th></tr>
            <tr><td>Data</td></tr>
        </table>
        <a href="#" title="Descriptive link">Informative link text</a>
        <section>Content section</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 100
        assert len(warnings) == 0
    
    def test_images_without_alt_text(self):
        """Test penalty for images without alt text."""
        html_content = """
        <h1>Title</h1>
        <img src="test1.jpg">
        <img src="test2.jpg">
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 90  # 100 - 10 (2 images * 5)
        assert any("image(s) manquent de description" in warning for warning in warnings)
    
    def test_no_h1_title(self):
        """Test penalty for missing H1 title."""
        html_content = """
        <h2>Subtitle</h2>
        <p>Content</p>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 90  # 100 - 10
        assert any("Document sans titre principal" in warning for warning in warnings)
    
    def test_multiple_h1_titles(self):
        """Test penalty for multiple H1 titles."""
        html_content = """
        <h1>First Title</h1>
        <h1>Second Title</h1>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 95  # 100 - 5
        assert any("Plusieurs titres H1" in warning for warning in warnings)
    
    def test_tables_without_accessibility(self):
        """Test penalty for tables without accessibility attributes."""
        html_content = """
        <h1>Title</h1>
        <table>
            <tr><th>Header</th></tr>
            <tr><td>Data</td></tr>
        </table>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 95  # 100 - 5
        assert any("tableau(x) sans attributs" in warning for warning in warnings)
    
    def test_generic_link_text(self):
        """Test penalty for generic link text."""
        html_content = """
        <h1>Title</h1>
        <a href="#">cliquez ici</a>
        <a href="#">ici</a>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 96  # 100 - 4 (2 links * 2)
        assert any("lien(s) avec texte peu descriptif" in warning for warning in warnings)
    
    def test_no_section_structure(self):
        """Test penalty for missing section structure."""
        html_content = """
        <h1>Title</h1>
        <p>Content without sections</p>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 95  # 100 - 5
        assert any("Document sans structure de sections" in warning for warning in warnings)
    
    def test_minimum_score_zero(self):
        """Test that score cannot go below zero."""
        html_content = """
        <img src="1.jpg"><img src="2.jpg"><img src="3.jpg"><img src="4.jpg"><img src="5.jpg">
        <img src="6.jpg"><img src="7.jpg"><img src="8.jpg"><img src="9.jpg"><img src="10.jpg">
        <table></table><table></table><table></table><table></table>
        <a href="#">ici</a><a href="#">ici</a><a href="#">ici</a><a href="#">ici</a><a href="#">ici</a>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score >= 0


class TestIsBigTitle:
    """Test the is_big_title function."""
    
    def test_is_big_title_not_text_block(self):
        """Test with non-text block."""
        block = {'type': 1, 'lines': []}
        mock_doc = Mock()
        
        result = is_big_title(block, mock_doc)
        assert result is False
    
    def test_is_big_title_no_lines(self):
        """Test with block having no lines."""
        block = {'type': 0, 'lines': []}
        mock_doc = Mock()
        
        result = is_big_title(block, mock_doc)
        assert result is False
    
    def test_is_big_title_with_large_font(self):
        """Test with block having large font."""
        block = {
            'type': 0,
            'lines': [
                {
                    'spans': [
                        {'size': 18, 'text': 'Big Title'}
                    ]
                }
            ]
        }
        
        mock_page = Mock()
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'lines': [
                        {
                            'spans': [
                                {'size': 12, 'text': 'Normal text'},
                                {'size': 18, 'text': 'Big Title'}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_doc = [mock_page]
        
        result = is_big_title(block, mock_doc)
        assert result is True
    
    def test_is_big_title_exception_handling(self):
        """Test exception handling in is_big_title."""
        block = {
            'type': 0,
            'lines': [
                {
                    'spans': [
                        {'text': 'No size attribute'}
                    ]
                }
            ]
        }
        mock_doc = Mock()
        
        with patch('server_enhanced.logger') as mock_logger:
            result = is_big_title(block, mock_doc)
            assert result is False
            mock_logger.warning.assert_called()


class TestProcessTextBlock:
    """Test the process_text_block function."""
    
    def test_process_text_block_simple(self):
        """Test processing simple text block."""
        block = {
            'lines': [
                {
                    'spans': [
                        {'text': 'Simple text', 'bbox': [0, 0, 100, 20]}
                    ]
                }
            ]
        }
        html_output = []
        mock_find_link = Mock(return_value=None)
        mock_doc = Mock()
        
        with patch('server_enhanced.is_big_title', return_value=False):
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 1
        assert '<p>Simple text</p>' in html_output[0]
    
    def test_process_text_block_with_link(self):
        """Test processing text block with link."""
        block = {
            'lines': [
                {
                    'spans': [
                        {'text': 'Link text', 'bbox': [0, 0, 100, 20]}
                    ]
                }
            ]
        }
        html_output = []
        mock_find_link = Mock(return_value='https://example.com')
        mock_doc = Mock()
        
        with patch('server_enhanced.is_big_title', return_value=False):
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 1
        assert '<a href="https://example.com"' in html_output[0]
    
    def test_process_text_block_bullet_points(self):
        """Test processing text block with bullet points."""
        block = {
            'lines': [
                {
                    'spans': [
                        {'text': '• First item • Second item', 'bbox': [0, 0, 100, 20]}
                    ]
                }
            ]
        }
        html_output = []
        mock_find_link = Mock(return_value=None)
        mock_doc = Mock()
        
        with patch('server_enhanced.is_big_title', return_value=False):
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert '<ul>' in html_output
        assert '<li>First item</li>' in html_output
        assert '<li>Second item</li>' in html_output
        assert '</ul>' in html_output
    
    def test_process_text_block_title(self):
        """Test processing text block as title."""
        block = {
            'lines': [
                {
                    'spans': [
                        {'text': 'Big Title', 'bbox': [0, 0, 100, 20]}
                    ]
                }
            ]
        }
        html_output = []
        mock_find_link = Mock(return_value=None)
        mock_doc = Mock()
        
        with patch('server_enhanced.is_big_title', return_value=True):
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 1
        assert '<h3>Big Title</h3>' in html_output[0]
    
    def test_process_text_block_empty(self):
        """Test processing empty text block."""
        block = {
            'lines': [
                {
                    'spans': [
                        {'text': '   ', 'bbox': [0, 0, 100, 20]}
                    ]
                }
            ]
        }
        html_output = []
        mock_find_link = Mock(return_value=None)
        mock_doc = Mock()
        
        process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 0


class TestProcessImageBlock:
    """Test the process_image_block function."""
    
    def test_process_image_block_success(self):
        """Test successful image processing."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        block = {
            'image': img_data
        }
        html_output = []
        
        with patch('server_enhanced.safe_ocr_extract', return_value='Test image alt text'):
            process_image_block(block, html_output)
        
        assert len(html_output) == 1
        assert '<figure role="img">' in html_output[0]
        assert 'alt="Test image alt text"' in html_output[0]
        assert '<figcaption>Test image alt text</figcaption>' in html_output[0]
        assert 'data:image/png;base64,' in html_output[0]
    
    def test_process_image_block_no_image(self):
        """Test processing block with no image."""
        block = {}
        html_output = []
        
        process_image_block(block, html_output)
        
        assert len(html_output) == 0
    
    def test_process_image_block_exception(self):
        """Test image processing with exception."""
        block = {
            'image': b'invalid image data'
        }
        html_output = []
        
        with patch('server_enhanced.logger') as mock_logger:
            process_image_block(block, html_output)
        
        assert len(html_output) == 1
        assert '[Image non disponible]' in html_output[0]
        mock_logger.warning.assert_called()


class TestAPIEndpoints:
    """Test the FastAPI endpoints."""
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "running" in data["message"]
    
    def test_convert_no_file(self):
        """Test convert endpoint with no file."""
        response = client.post("/convert")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_convert_invalid_file_type(self):
        """Test convert endpoint with invalid file type."""
        file_content = b"fake content"
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        response = client.post("/convert", files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_convert_file_too_large(self):
        """Test convert endpoint with file too large."""
        # Create a file larger than MAX_FILE_SIZE
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        files = {"file": ("test.pdf", large_content, "application/pdf")}
        
        response = client.post("/convert", files=files)
        assert response.status_code == 400
        assert "File size too large" in response.json()["detail"]
    
    @patch('server_enhanced.pdf_to_accessible_html')
    @patch('server_enhanced.calculate_accessibility_score')
    def test_convert_success(self, mock_calc_score, mock_pdf_convert):
        """Test successful PDF conversion."""
        mock_pdf_convert.return_value = ("<html>Test HTML</html>", "Test Title")
        mock_calc_score.return_value = (95, ["Warning message"])
        
        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        
        response = client.post("/convert", files=files)
        assert response.status_code == 200
        
        data = response.json()
        assert data["html"] == "<html>Test HTML</html>"
        assert data["title"] == "Test Title"
        assert data["accessibilityScore"] == 95
        assert data["warnings"] == ["Warning message"]
    
    @patch('server_enhanced.pdf_to_accessible_html')
    def test_convert_pdf_error(self, mock_pdf_convert):
        """Test PDF conversion with error."""
        mock_pdf_convert.side_effect = Exception("PDF conversion failed")
        
        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        
        response = client.post("/convert", files=files)
        assert response.status_code == 500
        assert "Erreur interne du serveur" in response.json()["detail"]


class TestPdfToAccessibleHtml:
    """Test the pdf_to_accessible_html function."""
    
    @patch('server_enhanced.fitz.open')
    def test_pdf_to_accessible_html_success(self, mock_fitz_open):
        """Test successful PDF to HTML conversion."""
        # Mock page
        mock_page = Mock()
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'bbox': [0, 0, 100, 20],
                    'lines': [
                        {
                            'spans': [
                                {'text': 'Test content', 'bbox': [0, 0, 100, 20]}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_page.get_links.return_value = []
        
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.metadata = {'title': 'Test Document'}
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            html_content, title = pdf_to_accessible_html(tmp_path)
            
            assert title == 'Test Document'
            assert '<html lang="fr">' in html_content
            assert '<title>Test Document - Version Accessible</title>' in html_content
            assert 'Test content' in html_content
            
        finally:
            os.unlink(tmp_path)
            mock_doc.close.assert_called_once()
    
    @patch('server_enhanced.fitz.open')
    def test_pdf_to_accessible_html_no_title(self, mock_fitz_open):
        """Test PDF conversion with no title in metadata."""
        # Mock page
        mock_page = Mock()
        mock_page.get_text.return_value = {'blocks': []}
        mock_page.get_links.return_value = []
        
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.metadata = {}
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            html_content, title = pdf_to_accessible_html(tmp_path)
            
            # Title should be derived from filename
            expected_title = os.path.splitext(os.path.basename(tmp_path))[0]
            assert title == expected_title
            
        finally:
            os.unlink(tmp_path)
    
    @patch('server_enhanced.fitz.open')
    def test_pdf_to_accessible_html_exception(self, mock_fitz_open):
        """Test PDF conversion with exception."""
        mock_fitz_open.side_effect = Exception("Cannot open PDF")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with pytest.raises(Exception) as exc_info:
                pdf_to_accessible_html(tmp_path)
            assert "Erreur lors de la conversion du PDF" in str(exc_info.value)
            
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__])
