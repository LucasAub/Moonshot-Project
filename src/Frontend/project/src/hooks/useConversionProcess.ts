import { useState } from 'react';
import { ConversionStatus } from '../types/conversion';
import { convertPdfToHtml } from '../utils/api';

export const useConversionProcess = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [htmlResult, setHtmlResult] = useState<string>('');
  const [documentTitle, setDocumentTitle] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleFileChange = (selectedFile: File) => {
    setFile(selectedFile);
    // Reset state when a new file is selected
    setStatus('idle');
    setHtmlResult('');
    setDocumentTitle('');
    setErrorMessage('');
  };

  const handleConversion = async () => {
    if (!file) return;
    
    try {
      setStatus('processing');
      
      // Call API to convert PDF to HTML
      const result = await convertPdfToHtml(file);
      
      // Set the conversion result
      setHtmlResult(result.html);
      
      // Set document title if available
      if (result.title) {
        setDocumentTitle(result.title);
      }
      
      setStatus('success');
    } catch (error) {
      console.error('Conversion error:', error);
      setStatus('error');
      setErrorMessage(
        error instanceof Error 
          ? error.message 
          : 'Failed to convert PDF. Please try again with a different file.'
      );
    }
  };

  const resetConversion = () => {
    setFile(null);
    setStatus('idle');
    setHtmlResult('');
    setDocumentTitle('');
    setErrorMessage('');
  };

  return {
    file,
    status,
    htmlResult,
    documentTitle,
    errorMessage,
    handleFileChange,
    handleConversion,
    resetConversion,
  };
};