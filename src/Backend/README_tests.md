# Unit Tests - PDF to HTML Converter

## Description
This file contains unit tests for the backend server `server_enhanced.py`.

## Included Tests

### 🔗 API Endpoint Tests
- `test_health_endpoint()` - Verifies the `/health` endpoint works
- `test_root_endpoint()` - Verifies the root endpoint `/` works

### 🏷️ HTML Tag Tests
- `test_html_tags_conversion()` - Verifies HTML tags are correctly generated
- `test_is_big_title_function()` - Tests big title detection

### 🖼️ Image Processing Tests
- `test_image_processing()` - Verifies images are properly read and converted
- `test_safe_ocr_function()` - Tests the safe OCR function

### 📄 File Validation Tests
- `test_convert_endpoint_no_file()` - Test without file
- `test_convert_endpoint_wrong_file_type()` - Test with wrong file type
- `test_convert_endpoint_empty_file()` - Test with empty file
- `test_convert_endpoint_valid_pdf()` - Test with valid PDF

## How to Run Tests

### Method 1: Automatic Script
```bash
python run_tests.py
```

### Method 2: Direct Pytest
```bash
python -m pytest test_server.py -v
```

### Method 3: Specific Test
```bash
python -m pytest test_server.py::test_html_tags_conversion -v
```

## Prerequisites
- pytest
- httpx
- fastapi
- PyMuPDF (fitz)
- PIL (Pillow)
- pytesseract

## Dependency Installation
```bash
pip install pytest httpx
```

## Expected Results
All tests should pass (10/10). The tests verify:
- Correct HTML tag generation
- Image processing with OCR
- Input file validation
- API endpoints functionality
- Error handling
