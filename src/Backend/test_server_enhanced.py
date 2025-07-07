"""
Comprehensive Unit Tests for server_enhanced.py

This module contains extensive unit tests for the PDF to Accessible HTML
Converter FastAPI server. The tests cover all major functionality including:

- Cross-platform Tesseract OCR configuration
- File validation and security checks
- OCR text extraction with error handling
- Accessibility scoring algorithm
- PDF text and image processing
- FastAPI endpoint testing
- Error handling and edge cases

Test Structure:
- Uses pytest framework with class-based organization
- Extensive mocking to avoid external dependencies
- Comprehensive assertions for behavior verification
- Error simulation for robustness testing
- Cross-platform compatibility testing

Coverage: 87% of server_enhanced.py code with 41 test cases

Author: Moonshot Project Team
Date: July 2025
Testing Framework: pytest with FastAPI TestClient
"""

# Standard library imports for testing utilities
import base64
import os
import tempfile
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

# Third-party testing imports
import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from PIL import Image
import fitz

# Import the module under test and all its components
from server_enhanced import (
    MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    app,
    calculate_accessibility_score,
    configure_tesseract,
    is_big_title,
    pdf_to_accessible_html,
    process_image_block,
    process_text_block,
    safe_ocr_extract,
    validate_file,
)

# Create FastAPI test client for endpoint testing
client = TestClient(app)


class TestConfigureTesseract:
    """
    Test suite for the configure_tesseract function.
    
    This class tests the cross-platform configuration of Tesseract OCR,
    ensuring proper setup on Windows, macOS, and Linux systems with
    various installation scenarios.
    
    Test Coverage:
    - Windows: Path detection in common installation directories
    - Windows: Handling when Tesseract is not found
    - macOS: Environment variable configuration
    - Linux: Default system configuration
    """
    
    @patch('server_enhanced.platform.system')
    @patch('server_enhanced.os.path.exists')
    @patch('server_enhanced.os.getenv')
    def test_configure_tesseract_windows_found(self, mock_getenv, mock_exists, mock_platform):
        """
        Test Tesseract configuration on Windows when installation is found.
        
        Verifies that the function correctly identifies and configures
        Tesseract when installed in standard Windows locations.
        """
        mock_platform.return_value = "Windows"
        mock_getenv.return_value = "TestUser"
        # Simulate finding Tesseract in Program Files
        mock_exists.side_effect = lambda path: "Program Files\\Tesseract-OCR" in path
        
        with patch('server_enhanced.pytesseract.pytesseract') as mock_pytesseract:
            configure_tesseract()
            # Verify that tesseract_cmd was set
            assert mock_pytesseract.tesseract_cmd is not None
    
    @patch('server_enhanced.platform.system')
    @patch('server_enhanced.os.path.exists')
    def test_configure_tesseract_windows_not_found(self, mock_exists, mock_platform):
        """
        Test Tesseract configuration on Windows when installation is not found.
        
        Verifies that the function handles missing Tesseract gracefully
        and logs appropriate warnings.
        """
        mock_platform.return_value = "Windows"
        mock_exists.return_value = False  # No Tesseract found
        
        with patch('server_enhanced.logger') as mock_logger:
            configure_tesseract()
            # Verify warning was logged
            mock_logger.warning.assert_called()
    
    @patch('server_enhanced.platform.system')
    @patch('server_enhanced.os.path.exists')
    def test_configure_tesseract_macos(self, mock_exists, mock_platform):
        """
        Test Tesseract configuration on macOS with Homebrew installation.
        
        Verifies proper environment variable setup for tessdata location.
        """
        mock_platform.return_value = "Darwin"
        mock_exists.return_value = True
        
        with patch('server_enhanced.os.environ') as mock_environ:
            configure_tesseract()
            # Verify environment variable configuration was attempted
            assert 'TESSDATA_PREFIX' in mock_environ or mock_environ.__setitem__.called
    
    @patch('server_enhanced.platform.system')
    def test_configure_tesseract_linux(self, mock_platform):
        """
        Test Tesseract configuration on Linux (no special configuration needed).
        
        Verifies that Linux systems don't require special configuration
        since Tesseract is typically available in PATH.
        """
        mock_platform.return_value = "Linux"
        # Should complete without raising exceptions
        configure_tesseract()


class TestValidateFile:
    """
    Test suite for the validate_file function.
    
    This class tests file validation logic including security checks,
    file type verification, and error handling for various upload scenarios.
    
    Test Coverage:
    - Missing filename handling
    - Invalid file type rejection
    - Valid PDF file acceptance
    - Case-insensitive extension checking
    """
    
    def test_validate_file_no_filename(self):
        """
        Test validation behavior when no filename is provided.
        
        Verifies that the function properly rejects uploads without
        a filename and raises appropriate HTTP exceptions.
        """
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        
        with pytest.raises(Exception) as exc_info:
            validate_file(mock_file)
        assert "No file provided" in str(exc_info.value)
    
    def test_validate_file_invalid_extension(self):
        """
        Test validation behavior with unsupported file types.
        
        Verifies that non-PDF files are rejected with appropriate
        error messages listing allowed file types.
        """
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"  # Invalid file type
        
        with pytest.raises(Exception) as exc_info:
            validate_file(mock_file)
        assert "Invalid file type" in str(exc_info.value)
    
    def test_validate_file_valid_pdf(self):
        """
        Test validation behavior with valid PDF files.
        
        Verifies that properly formatted PDF files pass validation
        without raising exceptions.
        """
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        
        # Should complete without raising exceptions
        validate_file(mock_file)
    
    def test_validate_file_case_insensitive(self):
        """
        Test that file extension validation is case-insensitive.
        
        Verifies that PDF files with uppercase extensions are
        accepted for better user experience.
        """
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.PDF"  # Uppercase extension
        
        # Should complete without raising exceptions
        validate_file(mock_file)


class TestSafeOcrExtract:
    """
    Test suite for the safe_ocr_extract function.
    
    This class tests OCR text extraction with comprehensive error handling,
    language support, and fallback behavior for various scenarios.
    
    Test Coverage:
    - Successful text extraction
    - Empty/whitespace-only results
    - OCR processing exceptions
    - Custom language parameter support
    """
    
    @patch('server_enhanced.pytesseract.image_to_string')
    def test_safe_ocr_extract_success(self, mock_ocr):
        """
        Test successful OCR text extraction from images.
        
        Verifies that text is properly extracted and whitespace
        is trimmed from OCR results.
        """
        mock_ocr.return_value = "  Extracted text  "  # Text with whitespace
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image)
        assert result == "Extracted text"  # Whitespace should be trimmed
        mock_ocr.assert_called_once_with(mock_image, lang="eng")
    
    @patch('server_enhanced.pytesseract.image_to_string')
    def test_safe_ocr_extract_empty_result(self, mock_ocr):
        """
        Test OCR behavior when no text is detected in images.
        
        Verifies that appropriate fallback text is returned
        when OCR produces empty or whitespace-only results.
        """
        mock_ocr.return_value = "   "  # Only whitespace
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image)
        assert result == "Image sans texte détectable"
    
    @patch('server_enhanced.pytesseract.image_to_string')
    @patch('server_enhanced.logger')
    def test_safe_ocr_extract_exception(self, mock_logger, mock_ocr):
        """
        Test OCR error handling when processing fails.
        
        Verifies that OCR exceptions are caught gracefully,
        logged appropriately, and fallback text is returned.
        """
        mock_ocr.side_effect = Exception("OCR failed")  # Simulate OCR failure
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image)
        assert result == "Image sans texte détectable"
        mock_logger.warning.assert_called()  # Error should be logged
    
    @patch('server_enhanced.pytesseract.image_to_string')
    def test_safe_ocr_extract_custom_language(self, mock_ocr):
        """
        Test OCR with custom language parameters.
        
        Verifies that different language codes are properly
        passed to the OCR engine for internationalization.
        """
        mock_ocr.return_value = "Texte français"
        mock_image = Mock(spec=Image.Image)
        
        result = safe_ocr_extract(mock_image, lang="fra")  # French language
        assert result == "Texte français"
        mock_ocr.assert_called_once_with(mock_image, lang="fra")


class TestCalculateAccessibilityScore:
    """
    Test suite for the calculate_accessibility_score function.
    
    This class tests the accessibility scoring algorithm that evaluates
    HTML content compliance with accessibility standards and generates
    appropriate warnings for issues found.
    
    Scoring Algorithm Test Coverage:
    - Perfect accessibility (100% score)
    - Images without alt text penalties (-5 points each, max -20)
    - Missing H1 title penalty (-10 points)
    - Multiple H1 titles penalty (-5 points)
    - Tables without accessibility attributes (-5 points each, max -15)
    - Generic link text penalties (-2 points each, max -10)
    - Missing section structure penalty (-5 points)
    - Score minimum threshold enforcement (0 minimum)
    """
    
    def test_perfect_accessibility_score(self):
        """
        Test HTML content that meets all accessibility criteria.
        
        Verifies that properly structured, accessible HTML receives
        a perfect score of 100 with no warnings.
        """
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
        """
        Test penalty calculation for images lacking alt text.
        
        Verifies that missing alt attributes result in proper
        score deductions and appropriate warning messages.
        """
        html_content = """
        <h1>Title</h1>
        <img src="test1.jpg">
        <img src="test2.jpg">
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 90  # 100 - 10 (2 images * 5 points each)
        assert any("image(s) manquent de description" in warning for warning in warnings)
    
    def test_no_h1_title(self):
        """
        Test penalty for documents missing primary heading.
        
        Verifies that documents without H1 titles receive
        appropriate score deductions for poor structure.
        """
        html_content = """
        <h2>Subtitle</h2>
        <p>Content</p>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 90  # 100 - 10
        assert any("Document sans titre principal" in warning for warning in warnings)
    
    def test_multiple_h1_titles(self):
        """
        Test penalty for documents with multiple H1 titles.
        
        Verifies that multiple H1 elements result in score
        deductions for unclear document structure.
        """
        html_content = """
        <h1>First Title</h1>
        <h1>Second Title</h1>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 95  # 100 - 5
        assert any("Plusieurs titres H1" in warning for warning in warnings)
    
    def test_tables_without_accessibility(self):
        """
        Test penalty for tables lacking accessibility attributes.
        
        Verifies that tables without proper ARIA labels or roles
        receive score deductions and warnings.
        """
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
        """
        Test penalty for links with non-descriptive text.
        
        Verifies that generic link text like "click here" results
        in appropriate score deductions and warnings.
        """
        html_content = """
        <h1>Title</h1>
        <a href="#">cliquez ici</a>
        <a href="#">ici</a>
        <section>Content</section>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 96  # 100 - 4 (2 links * 2 points each)
        assert any("lien(s) avec texte peu descriptif" in warning for warning in warnings)
    
    def test_no_section_structure(self):
        """
        Test penalty for documents lacking semantic section structure.
        
        Verifies that documents without section elements receive
        score deductions for poor semantic organization.
        """
        html_content = """
        <h1>Title</h1>
        <p>Content without sections</p>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score == 95  # 100 - 5
        assert any("Document sans structure de sections" in warning for warning in warnings)
    
    def test_minimum_score_zero(self):
        """
        Test that accessibility scores cannot go below zero.
        
        Verifies that documents with numerous accessibility issues
        have their scores capped at 0 to prevent negative values.
        """
        html_content = """
        <img src="1.jpg"><img src="2.jpg"><img src="3.jpg"><img src="4.jpg"><img src="5.jpg">
        <img src="6.jpg"><img src="7.jpg"><img src="8.jpg"><img src="9.jpg"><img src="10.jpg">
        <table></table><table></table><table></table><table></table>
        <a href="#">ici</a><a href="#">ici</a><a href="#">ici</a><a href="#">ici</a><a href="#">ici</a>
        """
        
        score, warnings = calculate_accessibility_score(html_content)
        assert score >= 0  # Score should never be negative


class TestIsBigTitle:
    """
    Test suite for the is_big_title function.
    
    This class tests the title detection algorithm that analyzes font sizes
    to determine if text blocks should be treated as headings in HTML output.
    
    Test Coverage:
    - Non-text block handling
    - Empty block handling
    - Font size comparison logic
    - Error handling for malformed PDF data
    """
    
    def test_is_big_title_not_text_block(self):
        """
        Test behavior with non-text blocks (e.g., image blocks).
        
        Verifies that the function correctly identifies and rejects
        non-text blocks without attempting title analysis.
        """
        block = {'type': 1, 'lines': []}  # Type 1 = image block
        mock_doc = Mock()
        
        result = is_big_title(block, mock_doc)
        assert result is False
    
    def test_is_big_title_no_lines(self):
        """
        Test behavior with text blocks containing no lines.
        
        Verifies that empty text blocks are correctly identified
        and don't trigger title detection logic.
        """
        block = {'type': 0, 'lines': []}  # Type 0 = text block, but empty
        mock_doc = Mock()
        
        result = is_big_title(block, mock_doc)
        assert result is False
    
    def test_is_big_title_with_large_font(self):
        """
        Test title detection with blocks containing large fonts.
        
        Verifies that text blocks with font sizes at or near the
        document maximum are correctly identified as titles.
        """
        block = {
            'type': 0,
            'lines': [
                {
                    'spans': [
                        {'size': 18, 'text': 'Big Title'}  # Large font size
                    ]
                }
            ]
        }
        
        # Mock document with mixed font sizes
        mock_page = Mock()
        mock_page.get_text.return_value = {
            'blocks': [
                {
                    'type': 0,
                    'lines': [
                        {
                            'spans': [
                                {'size': 12, 'text': 'Normal text'},  # Regular text
                                {'size': 18, 'text': 'Big Title'}    # Title text
                            ]
                        }
                    ]
                }
            ]
        }
        mock_doc = [mock_page]
        
        result = is_big_title(block, mock_doc)
        assert result is True  # Should be detected as title
    
    def test_is_big_title_exception_handling(self):
        """
        Test error handling for malformed PDF data.
        
        Verifies that the function gracefully handles PDF parsing
        errors and malformed data structures without crashing.
        """
        block = {
            'type': 0,
            'lines': [
                {
                    'spans': [
                        {'text': 'No size attribute'}  # Missing 'size' key
                    ]
                }
            ]
        }
        mock_doc = Mock()
        
        with patch('server_enhanced.logger') as mock_logger:
            result = is_big_title(block, mock_doc)
            assert result is False
            mock_logger.warning.assert_called()  # Error should be logged


class TestProcessTextBlock:
    """
    Test suite for the process_text_block function.
    
    This class tests text block processing including link detection,
    bullet point conversion, title identification, and HTML generation.
    
    Test Coverage:
    - Simple text paragraph processing
    - Link detection and conversion
    - Bullet point list generation
    - Title vs paragraph determination
    - Empty block handling
    """
    
    def test_process_text_block_simple(self):
        """
        Test processing of simple text blocks into HTML paragraphs.
        
        Verifies that basic text content is properly converted to
        HTML paragraph elements with correct content.
        """
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
        mock_find_link = Mock(return_value=None)  # No links found
        mock_doc = Mock()
        
        with patch('server_enhanced.is_big_title', return_value=False):
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 1
        assert '<p>Simple text</p>' in html_output[0]
    
    def test_process_text_block_with_link(self):
        """
        Test processing of text blocks containing PDF links.
        
        Verifies that linked text is properly converted to HTML
        anchor elements with security attributes.
        """
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
        mock_find_link = Mock(return_value='https://example.com')  # Link found
        mock_doc = Mock()
        
        with patch('server_enhanced.is_big_title', return_value=False):
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 1
        assert '<a href="https://example.com"' in html_output[0]
    
    def test_process_text_block_bullet_points(self):
        """
        Test conversion of bullet point text to HTML unordered lists.
        
        Verifies that text containing bullet characters is properly
        converted to semantic HTML list structures.
        """
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
        
        # Should create a proper HTML list structure
        assert '<ul>' in html_output
        assert '<li>First item</li>' in html_output
        assert '<li>Second item</li>' in html_output
        assert '</ul>' in html_output
    
    def test_process_text_block_title(self):
        """
        Test processing of text blocks identified as titles.
        
        Verifies that title blocks are converted to appropriate
        heading elements rather than paragraphs.
        """
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
        
        with patch('server_enhanced.is_big_title', return_value=True):  # Detected as title
            process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 1
        assert '<h3>Big Title</h3>' in html_output[0]
    
    def test_process_text_block_empty(self):
        """
        Test handling of empty or whitespace-only text blocks.
        
        Verifies that blocks with no meaningful content don't
        generate empty HTML elements.
        """
        block = {
            'lines': [
                {
                    'spans': [
                        {'text': '   ', 'bbox': [0, 0, 100, 20]}  # Only whitespace
                    ]
                }
            ]
        }
        html_output = []
        mock_find_link = Mock(return_value=None)
        mock_doc = Mock()
        
        process_text_block(block, html_output, mock_find_link, mock_doc)
        
        assert len(html_output) == 0  # No output for empty content


class TestProcessImageBlock:
    """
    Test suite for the process_image_block function.
    
    This class tests image processing including base64 conversion,
    OCR text extraction for accessibility, and error handling.
    
    Test Coverage:
    - Successful image processing with OCR
    - Missing image data handling
    - Exception handling with fallback content
    """
    
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
    """
    Test suite for FastAPI endpoint functionality.
    
    This class tests the REST API endpoints including file upload handling,
    validation, conversion processing, and error responses.
    
    Test Coverage:
    - Health check endpoint functionality
    - File upload validation and error handling
    - File size limit enforcement
    - Successful PDF conversion workflow
    - Error handling and appropriate HTTP status codes
    """
    
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
    """
    Test suite for the main PDF conversion function.
    
    This class tests the core PDF to HTML conversion functionality including
    document processing, metadata extraction, and comprehensive error handling.
    
    Test Coverage:
    - Successful PDF conversion with metadata
    - Fallback title generation from filename
    - Document-level error handling and cleanup
    """
    
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


# Entry point for running tests directly
if __name__ == "__main__":
    """
    Direct execution entry point for the test suite.
    
    When this file is run directly (python test_server_enhanced.py),
    it will execute all tests using pytest with the current file as the target.
    
    This provides a convenient way to run just these tests without needing
    to specify the file path to pytest explicitly.
    """
    pytest.main([__file__])
