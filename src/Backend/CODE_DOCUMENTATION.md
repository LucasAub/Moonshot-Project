# Code Documentation - server_enhanced.py

## Overview

The `server_enhanced.py` file is a FastAPI web server that converts PDF files to accessible HTML. It's designed to be understandable by developers who are not familiar with the codebase.

## Code Architecture

### 📋 General Structure

```
server_enhanced.py
├── 📦 Imports and Configuration
├── 🔧 Tesseract OCR Configuration
├── 🌐 FastAPI Configuration
├── 🎨 CSS Styles
├── 🛠️ Utility Functions
├── 🔄 Main Conversion Function
├── 🌍 API Endpoints
└── 🚀 Server Startup
```

### 🔧 Main Components

#### 1. Tesseract OCR Configuration
- **Purpose**: Configure OCR to extract text from images
- **Cross-platform**: Windows, macOS, Linux
- **Error handling**: Works even if Tesseract is not installed

#### 2. Utility Functions

##### `is_big_title(block, doc)`
- **Role**: Determines if a text block is a main title
- **Method**: Compares the block's font size with the document's
- **Result**: `True` = title (`<h2>` tag), `False` = paragraph (`<p>` tag)

##### `safe_ocr(pil_img)`
- **Role**: Safely extracts text from an image
- **Safety**: Never crashes, even if OCR fails
- **Languages**: Configured for French

#### 3. Main Conversion Function

##### `pdf_to_accessible_html(pdf_path)`
**Step-by-step process:**

1. **PDF Opening** with PyMuPDF
2. **Metadata Extraction** (document title)
3. **Page-by-page Processing**:
   - Extract text blocks and images
   - Sort by position (top → bottom, left → right)
   - Detect hyperlinks
4. **HTML Generation** with semantic structure
5. **Cleanup** and document closure

#### 4. API Endpoints

##### `GET /` - Entry Point
- Verify server is running

##### `GET /health` - Diagnostics
- Server status
- OCR availability
- System information

##### `POST /convert` - Conversion
**Validation:**
- Filename present
- .pdf extension
- Non-empty file
- Size < 50MB

**Processing:**
- Temporary save
- PDF → HTML conversion
- Accessibility score calculation
- Automatic cleanup

## 🏗️ Data Flow

```
📄 PDF Upload
    ↓
🔍 Validation
    ↓
💾 Temporary File
    ↓
📖 PDF Reading (PyMuPDF)
    ↓
🔄 Page-by-Page Processing
    ├── 📝 Text Extraction
    ├── 🖼️ Image Processing (OCR)
    └── 🔗 Link Detection
    ↓
🎯 Semantic HTML Generation
    ↓
✅ Accessibility Score
    ↓
📤 JSON Response
    ↓
🗑️ Temporary Cleanup
```

## 🎯 Accessibility Features

### Score from 0 to 100 based on:
- ✅ **Images with descriptions** (alt text via OCR)
- ✅ **Heading structure** (unique H1, hierarchy)
- ✅ **Accessible tables** (ARIA attributes)
- ✅ **Navigation** (sections with labels)
- ✅ **Links** (automatic URL detection)

### Generated HTML Tags
- `<html lang="fr">` - Document language
- `<h1>` - Unique main title
- `<h2>` - Subtitles (detected by font size)
- `<section aria-label="Page X">` - Page navigation
- `<figure>` + `<figcaption>` - Images with descriptions
- `<ul>` + `<li>` - Bullet lists
- `<a href="">` - Hyperlinks

## 🛡️ Error Handling

### Protection Levels
1. **Input validation** - Invalid files → HTTP 400
2. **Safe processing** - OCR errors → Status messages
3. **Global handler** - Unexpected errors → Structured JSON
4. **Automatic cleanup** - Temporary files always deleted

### Handled Error Types
- 📁 Missing or invalid file
- 💾 Corrupted or unreadable PDF
- 🖼️ Non-processable images
- 🔤 OCR failure
- 💻 System issues

## 🚀 Usage

### Simple Startup
```bash
python server_enhanced.py
```

### Available Endpoints
```
GET  http://localhost:8000/        # API Info
GET  http://localhost:8000/health  # Diagnostics
POST http://localhost:8000/convert # Conversion
```

### Usage Example
```javascript
// Frontend JavaScript
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('/api/convert', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log(result.html); // Generated HTML
console.log(result.accessibilityScore); // Score 0-100
```

## 🔧 Required Dependencies

- **FastAPI** - Modern web framework
- **PyMuPDF** - PDF processing
- **Pillow** - Image manipulation
- **pytesseract** - OCR (optional)
- **uvicorn** - ASGI server

## 📝 Notes for Developers

- **Well-commented code** - Every function explained
- **Type hints** - Parameters and returns documented
- **Robust error handling** - No possible crashes
- **Unit tests** - Complete coverage
- **Cross-platform** - Windows, macOS, Linux
