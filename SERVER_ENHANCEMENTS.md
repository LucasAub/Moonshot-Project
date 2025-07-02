# Server Enhancements

## Overview
The `server.py` file has been significantly enhanced to improve reliability, security, and functionality.

## Key Improvements

### 1. Cross-Platform Compatibility
- **Tesseract Configuration**: Automatically detects and configures Tesseract OCR paths for Windows, macOS, and Linux
- **Windows Support**: Specific support for common Windows Tesseract installation paths
- **Error Handling**: Graceful handling when Tesseract is not found

### 2. Enhanced Security & Validation
- **File Validation**: Validates file type and size before processing
- **File Size Limits**: Maximum 50MB file size limit
- **Input Sanitization**: Better handling of malformed PDF files
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes

### 3. Improved HTML Generation
- **Modern HTML5**: Proper DOCTYPE and meta tags
- **Responsive Design**: Viewport meta tag for mobile compatibility
- **Enhanced CSS**: Better typography, spacing, and accessibility features
- **Semantic HTML**: Proper use of semantic elements (header, main, section, figure)

### 4. Better Accessibility
- **ARIA Labels**: Proper ARIA attributes for screen readers
- **Alt Text**: OCR-generated alt text for images
- **Link Accessibility**: Target="_blank" with rel="noopener noreferrer"
- **Keyboard Navigation**: Focus styles for keyboard users
- **Accessibility Scoring**: Enhanced scoring algorithm with detailed warnings

### 5. Enhanced Error Handling
- **Comprehensive Logging**: Detailed logging for debugging
- **Graceful Degradation**: Continues processing even if individual elements fail
- **Resource Cleanup**: Proper cleanup of temporary files and resources
- **Progress Tracking**: Logs progress through document processing

### 6. API Improvements
- **Health Check Endpoint**: `/health` endpoint for monitoring
- **Better Documentation**: OpenAPI/Swagger documentation
- **CORS Configuration**: Proper CORS setup for multiple origins
- **Type Hints**: Full type annotations for better code quality

### 7. Performance Optimizations
- **Lazy Loading**: Images use lazy loading attribute
- **Efficient Processing**: Better memory management during PDF processing
- **Parallel Processing**: Structured for potential future async improvements

## New Features

### Enhanced CSS Styling
- Modern typography with system fonts
- Better contrast and readability
- Responsive design principles
- Print-friendly styles
- Visual hierarchy with proper heading styles

### Improved OCR Integration
- Better error handling for OCR failures
- Language detection support
- Fallback text for failed OCR attempts

### Advanced PDF Processing
- Better title extraction from PDF metadata and content
- Improved bullet point detection and formatting
- Enhanced link detection and processing
- Proper handling of complex document structures

## Setup Instructions

### Prerequisites
1. Python 3.8+
2. Tesseract OCR (for image text extraction)

### Installation
1. Run `setup.ps1` (PowerShell) or `setup.bat` (Command Prompt)
2. This will:
   - Create a virtual environment
   - Install all dependencies
   - Check for Tesseract installation

### Running the Server
1. Run `run_server.ps1` or manually:
   ```bash
   venv\Scripts\activate
   cd src\Backend
   python server.py
   ```

2. Server will be available at `http://localhost:8000`
3. API documentation at `http://localhost:8000/docs`

## Dependencies
- `fastapi>=0.104.1` - Modern web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `PyMuPDF>=1.23.0` - PDF processing
- `Pillow>=10.0.0` - Image processing
- `pytesseract>=0.3.10` - OCR functionality
- `python-multipart>=0.0.6` - File upload support

## Configuration
The server automatically configures itself based on the operating system:
- Windows: Searches common Tesseract installation paths
- macOS: Uses Homebrew paths
- Linux: Uses system PATH

## Monitoring
- Health check endpoint: `GET /health`
- Detailed logging to console
- Accessibility scoring with specific warnings

## Error Handling
- Comprehensive error messages
- Proper HTTP status codes
- Graceful degradation for partial failures
- Resource cleanup on errors
