
# 📄 PDF Accessibility Conversion System

Transform inaccessible PDFs into semantically structured, screen reader-friendly HTML documents. This tool is designed for organizations and individuals committed to digital accessibility.

---

## 🧭 Overview

This project provides an automated solution to convert standard PDF documents into accessible HTML format, optimized for assistive technologies such as screen readers. It ensures proper semantic structure, alt-text generation, and streamlined user experience.

---

## 🚀 Features

- ✅ Drag-and-drop or file selection upload  
- ✅ OCR-based alt text generation (French supported)  
- ✅ Semantic HTML5 output with heading structure  
- ✅ Hyperlink and paragraph preservation  
- ✅ Lightweight, responsive web interface  
- ✅ Fully stateless backend (no data retained)

---

## 👥 Target Users

- Individuals with visual impairments using screen readers (JAWS, NVDA, VoiceOver)  
- Educational institutions and public administrations  
- Accessibility professionals and compliance teams

---

## ⚙️ Architecture

```
Client (HTML Upload UI) 
   │
   └──► FastAPI Backend (Python)
           ├─ PDF Parsing (PyMuPDF)
           ├─ OCR (Tesseract)
           ├─ Image Processing (PIL)
           └─ HTML Generator
```

---

## 🧪 API Usage

**Endpoint:** `POST /convert`  
**Input:** PDF file (`multipart/form-data`)  
**Output:** JSON containing:
- Converted semantic HTML
- Document metadata
- Processing status

**Error Handling:**  
Returns HTTP error codes with descriptive messages.

---

## 🧠 Algorithms Used

- **Block Sorting Algorithm** – Ensures correct reading order via spatial coordinates  
- **Heading Detection** – Font size-based title detection  
- **OCR Integration** – Tesseract with French model for alt text generation  
- **Hyperlink Mapping** – Bounding-box overlap for anchor tag preservation

---

## 📊 Known Limitations

- Tables are not yet converted to semantic HTML tables  
- Complex multi-column PDFs may lose logical reading order  
- Forms and equations are not processed interactively  
- No visual accessibility enhancements (focus is on screen reader navigation)

---

## 🛠️ Technology Stack

| Layer         | Tool/Library       |
|---------------|--------------------|
| Backend       | FastAPI (Python)   |
| PDF Parsing   | PyMuPDF (fitz)     |
| OCR Engine    | Tesseract (via `pytesseract`) |
| Images        | PIL (Python Imaging Library) |
| Server        | Uvicorn (ASGI)     |
| Deployment    | Dockerized setup   |

---

## 📦 Deployment

- Python 3.8+ environment  
- Docker containerization  
- French language data for Tesseract  
- Stateless by design – no persistent storage  
- Configurable via environment variables

---

## 🔐 Security & Privacy

- File type and size validation  
- Temporary file cleanup after processing  
- No document saved permanently  
- No external API calls – 100% local processing

---

## 📈 Performance

- Processes most PDFs in under 60 seconds  
- Asynchronous file handling (non-blocking)  
- Memory-efficient image processing  
- Compatible with horizontal scaling

---

## 🧪 Testing Strategy

- Manual validation using screen readers (JAWS, NVDA)  
- Real-world document testing  
- Iterative accessibility validation  
- Accessibility score feedback

---

## 📌 Future Enhancements

| Priority | Feature                                       |
|----------|-----------------------------------------------|
| 🔥 High   | Table structure recognition and conversion   |
| 🧠 Mid    | Machine learning for better heading detection|
| ☁️ Mid    | Cloud integration and batch processing       |
| 🎯 Long   | NLP for summarization and advanced alt text  |

---

## 📅 Project Timeline

- **March 2025** – Requirements analysis and scope definition  
- **April 2025** – Pivot to structural accessibility only  
- **May 2025** – Core development, OCR, and HTML output  
- **June 2025** – Testing, optimization, and documentation

---

## 🤝 Contributing

Currently not open to contributions. Please reach out for collaboration opportunities.

---

## 🧾 License

This project is released under the MIT License.

---

## 🌍 Impact

The system empowers visually impaired users and organizations to bridge the accessibility gap, complying with WCAG 2.1, Section 508, and European Accessibility Act standards.

> “Making information accessible is not a feature. It’s a human right.”

---

## ✨ Acknowledgements

- Tesseract OCR open-source community  
- Accessibility advocacy organizations  
- Feedback from real screen reader users
