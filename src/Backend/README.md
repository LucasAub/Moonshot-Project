# PDF to HTML Converter - Backend Documentation

## 📋 Overview

This backend server converts PDF files to accessible HTML format using FastAPI, PyMuPDF, and OCR technology. It's designed with comprehensive documentation for developers at any skill level.

## 🏗️ Project Structure

```
Backend/
├── 📄 server_enhanced.py      # Main server (fully documented)
├── 📄 server.py               # Original server (legacy)
├── 🧪 test_server.py          # Unit tests
├── 🔧 run_tests.py            # Test runner script
├── ⚙️ pytest.ini             # Test configuration
├── 📚 CODE_DOCUMENTATION.md   # Detailed code architecture
└── 📝 README_tests.md         # Testing guide
```

## ✨ Features

### 🔄 PDF Processing
- **Text Extraction** - Preserves fonts, sizes, and layout
- **Image Processing** - OCR with Tesseract for accessibility
- **Link Detection** - Automatic hyperlink preservation
- **Structure Analysis** - Smart heading detection

### 🎯 Accessibility Compliance
- **Semantic HTML** - Proper tags (`<h1>`, `<h2>`, `<section>`, etc.)
- **Alt Text** - OCR-generated image descriptions
- **Navigation** - Page-by-page sections with ARIA labels
- **Scoring System** - 0-100 accessibility rating

### 🛡️ Robust Error Handling
- **Input Validation** - File type, size, content checks
- **Graceful Degradation** - Works without OCR if needed
- **JSON Responses** - Structured error messages
- **Automatic Cleanup** - No temporary file accumulation

### 🌐 Cross-Platform Support
- **Windows** - Auto-detects Tesseract installation
- **macOS** - Homebrew configuration
- **Linux** - Package manager support

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn PyMuPDF Pillow pytesseract
```

### 2. Start Server
```bash
python server_enhanced.py
```

### 3. Test API
```bash
# Health check
curl http://localhost:8000/health

# Convert PDF (using form data)
curl -X POST -F "file=@document.pdf" http://localhost:8000/convert
```

## 🧪 Testing

### Run All Tests
```bash
python run_tests.py
```

### Test Coverage
- ✅ **API Endpoints** - Health, root, conversion
- ✅ **HTML Generation** - Tags, structure, semantics  
- ✅ **Image Processing** - OCR, base64 encoding
- ✅ **File Validation** - Type, size, content checks
- ✅ **Error Handling** - Edge cases and failures

## 📊 API Reference

### Endpoints

#### `GET /`
**Purpose**: Server status check  
**Response**: Basic API information

#### `GET /health`
**Purpose**: Detailed diagnostics  
**Response**: 
```json
{
  "status": "healthy",
  "tesseract_available": true,
  "platform": "Windows"
}
```

#### `POST /convert`
**Purpose**: PDF to HTML conversion  
**Input**: PDF file (multipart/form-data)  
**Response**:
```json
{
  "html": "<html>...</html>",
  "title": "Document Title",
  "accessibilityScore": 85,
  "warnings": ["Some images lack descriptions"],
  "metadata": {
    "filename": "document.pdf",
    "size": 1024000,
    "tesseract_used": true
  }
}
```

## 🎨 Generated HTML Structure

```html
<html lang="fr">
  <head>
    <meta charset="UTF-8">
    <title>Document Title Accessible</title>
    <style>/* Accessibility CSS */</style>
  </head>
  <body>
    <h1>Document Title</h1>
    
    <section aria-label="Page 1">
      <h2>Chapter Title</h2>
      <p>Regular text content...</p>
      
      <figure>
        <img src="data:image/png;base64,..." alt="OCR description">
        <figcaption>OCR description</figcaption>
      </figure>
      
      <ul>
        <li>Bullet point item</li>
      </ul>
    </section>
  </body>
</html>
```

## 🔧 Configuration

### Tesseract OCR Setup

**Windows**: Auto-detected from common paths:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`

**macOS/Linux**: Uses system installation with TESSDATA_PREFIX

### File Limits
- **Max Size**: 50MB
- **Format**: PDF only
- **Validation**: Filename, content, extension

### CORS Configuration
- **Origins**: `localhost:5173`, `127.0.0.1:5173`
- **Methods**: All HTTP methods
- **Headers**: All headers allowed

## 📈 Accessibility Scoring

### Scoring Criteria
- **100 points**: Perfect accessibility
- **-10 points**: Missing image alt text
- **-10 points**: Tables without ARIA attributes
- **-5 points**: No main heading (H1)
- **-3 points**: Multiple H1 headings

### Automatic Checks
- ✅ Image descriptions via OCR
- ✅ Heading structure validation
- ✅ Semantic HTML compliance
- ✅ Navigation landmarks

## 🐛 Troubleshooting

### Common Issues

**"Tesseract not found"**
- Install Tesseract OCR for your OS
- Server works without OCR (reduced functionality)

**"File too large"**
- Max size is 50MB
- Consider compressing the PDF

**"JSON parse error"**
- Fixed with global exception handler
- All responses are valid JSON

**"CORS error"**
- Check frontend URL in CORS configuration
- Ensure ports match (frontend/backend)

## 🤝 Contributing

### Code Standards
- **Comprehensive comments** in English
- **Type hints** for all functions
- **Error handling** for all operations
- **Unit tests** for new features

### Testing Requirements
- All tests must pass (10/10)
- Coverage for new functionality
- Documentation updates required

## 📝 Documentation Files

- **`CODE_DOCUMENTATION.md`** - Detailed architecture guide
- **`README_tests.md`** - Complete testing documentation
- **`server_enhanced.py`** - Fully commented source code

## 🏆 Benefits

### For Developers
- **Easy to understand** - Comprehensive comments
- **Well tested** - 100% test coverage
- **Cross-platform** - Works everywhere
- **Error resilient** - Graceful failure handling

### For Users
- **Accessible output** - WCAG compliant HTML
- **Fast processing** - Optimized algorithms
- **Reliable service** - Robust error handling
- **Complete conversion** - Text, images, links preserved

---

*This documentation ensures anyone can understand, modify, and extend the PDF to HTML converter server.*
