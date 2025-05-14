import React, { useState, useRef } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';
import FileUploader from './FileUploader';
import ProgressStatus from './ProgressStatus';
import DocumentPreview from './DocumentPreview';
import { FileIcon, FileTextIcon } from 'lucide-react';

type ConversionStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

const PDFAccessibilityConverter: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [convertedDocUrl, setConvertedDocUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const { announceMessage } = useAccessibility();
  const formRef = useRef<HTMLFormElement>(null);

  const handleFileChange = (selectedFile: File | null) => {
    if (selectedFile) {
      setFile(selectedFile);
      setStatus('idle');
      setConvertedDocUrl(null);
      setErrorMessage('');
      setPreviewHtml(null);
      announceMessage(`Fichier PDF sélectionné : ${selectedFile.name}`, 'polite');
    } else {
      setFile(null);
      announceMessage('Aucun fichier sélectionné', 'polite');
    }
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
  
    setStatus("uploading")
    const form = new FormData()
    form.append("pdfFile", file)
  
    try {
      const res = await fetch("http://localhost:8000/convert", {
        method: "POST",
        body: form,
      })
      if (!res.ok) throw new Error(await res.text())
      const html = await res.text()
      setPreviewHtml(html)
      const blob = new Blob([html], { type: "text/html" })
      setConvertedDocUrl(URL.createObjectURL(blob))
      setStatus("success")
    } catch (err) {
      setStatus("error")
      setErrorMessage((err as Error).message)
    }
  }

  const resetForm = () => {
    if (formRef.current) {
      formRef.current.reset();
    }
    setFile(null);
    setStatus('idle');
    setConvertedDocUrl(null);
    setErrorMessage('');
    setPreviewHtml(null);
    announceMessage('Formulaire réinitialisé', 'polite');
  };

  return (
    <section className="max-w-2xl mx-auto">
      <header>
        <h1 className="text-2xl font-bold mb-4 text-gray-800" tabIndex={0}>
          Convertisseur de PDF Accessible
        </h1>
        <p className="mb-6 text-gray-600" tabIndex={0}>
          Cet outil convertit vos documents PDF en format HTML accessible pour les lecteurs d'écran.
        </p>
      </header>

      <form 
        ref={formRef}
        onSubmit={handleSubmit} 
        className="mb-8 space-y-6 border border-gray-200 rounded-lg p-6 bg-gray-50"
        aria-labelledby="form-heading"
      >
        <div className="sr-only" id="form-heading">Formulaire de conversion de PDF</div>
        
        <FileUploader 
          onFileChange={handleFileChange} 
          acceptedFileTypes=".pdf"
          isDisabled={status === 'uploading' || status === 'processing'}
        />
        
        {file && (
          <div className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded">
            <FileIcon className="text-blue-600" size={20} aria-hidden="true" />
            <span>{file.name}</span>
          </div>
        )}

        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={!file || status === 'uploading' || status === 'processing'}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-busy={status === 'uploading' || status === 'processing'}
          >
            Générer la version accessible
          </button>
          
          <button
            type="button"
            onClick={resetForm}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
            aria-label="Réinitialiser le formulaire"
          >
            Réinitialiser
          </button>
        </div>
      </form>

      <ProgressStatus status={status} errorMessage={errorMessage} />

      {convertedDocUrl && (
        <div className="mt-8 p-4 border border-green-200 rounded-lg bg-green-50">
          <h2 className="text-lg font-semibold mb-3 text-gray-800">Document Converti</h2>
          
          <div className="flex items-center space-x-2 mb-4">
            <FileTextIcon className="text-green-600" size={20} aria-hidden="true" />
            <a
              href={convertedDocUrl}
              download={`${file?.name.replace('.pdf', '')}-accessible.html`}
              className="text-blue-600 underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              aria-label={`Télécharger la version accessible de ${file?.name}`}
            >
              Télécharger la version HTML accessible
            </a>
          </div>
          
          {previewHtml && <DocumentPreview htmlContent={previewHtml} />}
        </div>
      )}
    </section>
  );
};

export default PDFAccessibilityConverter;