import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  file: File | null;
  onFileChange: (file: File) => void;
  onConvert: () => void;
  isProcessing: boolean;
  disabled: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  file,
  onFileChange,
  onConvert,
  isProcessing,
  disabled
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateFile = (file: File): boolean => {
    if (!file.type.includes('pdf')) {
      setFileError('Please upload a PDF file only');
      return false;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setFileError('File size exceeds 10MB limit');
      return false;
    }

    setFileError(null);
    return true;
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        onFileChange(droppedFile);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        onFileChange(selectedFile);
      }
    }
  };

  const handleButtonClick = () => {
    inputRef.current?.click();
  };

  return (
    <section className="mb-8">
      <div 
        className={`
          border-2 border-dashed rounded-lg p-8 text-center 
          transition-colors duration-200 
          ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'} 
          ${disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400 hover:bg-blue-50'}
        `}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={disabled ? undefined : handleDrop}
        aria-labelledby="upload-title"
        aria-describedby="upload-description"
      >
        <input
          ref={inputRef}
          type="file"
          id="file-upload"
          name="file-upload"
          className="hidden"
          accept=".pdf"
          onChange={handleChange}
          disabled={disabled}
          aria-invalid={fileError ? 'true' : 'false'}
        />
        
        <motion.div 
          initial={{ scale: 1 }}
          animate={{ scale: dragActive ? 1.05 : 1 }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex justify-center mb-4">
            <FileText 
              className="text-blue-500" 
              size={48} 
              aria-hidden="true" 
            />
          </div>

          <h2 id="upload-title" className="text-xl font-semibold mb-2">
            {file ? 'Selected PDF file' : 'Upload your PDF file'}
          </h2>
          
          <p id="upload-description" className="text-gray-600 mb-4">
            {file 
              ? `${file.name} (${(file.size / 1024).toFixed(1)} KB)` 
              : 'Drag and drop your file here, or click to browse'}
          </p>

          {!file && (
            <button
              type="button"
              className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg inline-flex items-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              onClick={handleButtonClick}
              disabled={disabled}
            >
              <Upload className="mr-2" size={18} aria-hidden="true" />
              Browse Files
            </button>
          )}

          {file && (
            <button
              type="button"
              className="bg-green-600 hover:bg-green-700 text-white py-2 px-6 rounded-lg inline-flex items-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:bg-gray-400"
              onClick={onConvert}
              disabled={disabled}
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" aria-hidden="true"></div>
                  Processing...
                </>
              ) : (
                <>
                  Generate Accessible HTML
                </>
              )}
            </button>
          )}
        </motion.div>
      </div>

      {fileError && (
        <motion.div 
          className="mt-2 text-red-600 flex items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <AlertCircle size={16} className="mr-1" aria-hidden="true" />
          <span id="file-error" role="alert">{fileError}</span>
        </motion.div>
      )}
      
      <div className="mt-4 text-sm text-gray-600">
        <p>
          <strong>Supported format:</strong> PDF files up to 10MB
        </p>
      </div>
    </section>
  );
};