
# 🧾 Accessible PDF to HTML Converter

This project is a **school capstone project** developed as part of an end-of-year assignment. Its goal is to improve **digital accessibility** by converting PDF files into **HTML documents readable by screen readers**.

## 🎯 Objective

Many PDF files are poorly structured and inaccessible for visually impaired users. This web application provides a simple tool to:

- 📄 **Upload a PDF** file
- 🔁 **Process its content** to detect structural elements
- 🧾 **Convert the file to HTML** in a format that is **screen-reader-friendly**

The resulting HTML document includes proper semantic structure to ensure better accessibility.

## ♿ Accessibility Enhancements

During conversion, the system applies multiple accessibility rules:

- ✅ **Headings**: Ensures titles are correctly marked with `<h1>`–`<h6>` tags rather than `<p>` or `<div>`.
- 🧮 **Tables**: Detects tables and ensures proper markup with `<table>`, `<thead>`, `<tbody>`, and `<th>`.
- 🖼️ **Images**: Adds or fixes **`alt` attributes** for images that are missing them.
- 📑 **Logical reading order**: Ensures that the document flow follows a logical and accessible structure.

## 🛠 Tech Stack

- **Frontend Framework**: React + Vite
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Linting**: ESLint + TypeScript ESLint

## 📦 Installation

```
git clone https://github.com/yourusername/pdf-accessibility-converter.git
cd pdf-accessibility-converter
npm install
```

## 🚀 Development

```
npm run dev
```

## 🔧 Build

```
npm run build
```

## 🔍 Preview Production Build

```
npm run preview
```

## 🧪 Folder Structure

```
src/
├── components/         # UI Components (Header, Footer, FileUpload, etc.)
├── hooks/              # Custom React hooks (conversion logic)
├── utils/              # Utility functions (e.g. API handler)
├── types/              # TypeScript type definitions
├── App.tsx             # Main application entry
├── main.tsx            # Root React render
```

## 📄 Output

The app returns a **clean HTML file** designed for screen reader compatibility. It can be used as a base for accessible publishing or further manual refinement.

## 📚 Educational Context

This project was developed as part of an academic assignment to explore real-world accessibility challenges and implement technical solutions using modern web tools. It aims to bridge the gap between common PDF formatting and web accessibility standards.

## 📄 License

This project is open-source and free to use.

---

## 🙌 Contributing

Feel free to open issues or submit pull requests for suggestions or improvements.
