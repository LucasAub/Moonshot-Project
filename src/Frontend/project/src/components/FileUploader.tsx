import React, { useRef, useState } from 'react';
import { UploadIcon } from 'lucide-react';

interface FileUploaderProps {
  onFileChange: (file: File | null) => void;
  acceptedFileTypes: string;
  isDisabled?: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ 
  onFileChange, 
  acceptedFileTypes,
  isDisabled = false 
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] || null;
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (file: File | null) => {
    if (!file) {
      onFileChange(null);
      return;
    }

    // Check if file is a PDF by both extension and MIME type
    const fileType = file.type;
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    if (fileType === 'application/pdf' || fileExtension === 'pdf') {
      onFileChange(file);
    } else {
      alert('Veuillez sélectionner un document PDF valide.');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onFileChange(null);
    }
  };

  const handleBrowseClick = () => {
    if (!isDisabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDisabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDisabled) setIsDragging(true);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (isDisabled) return;
    
    const file = e.dataTransfer.files?.[0] || null;
    validateAndSetFile(file);
  };

  return (
    <div className="space-y-2">
      <label 
        htmlFor="pdf-file" 
        className="block font-medium text-gray-700"
      >
        Sélectionner un document PDF à convertir
      </label>
      
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'} 
          ${isDisabled ? 'opacity-60 cursor-not-allowed' : 'hover:bg-gray-50'}`}
        onClick={handleBrowseClick}
        tabIndex={isDisabled ? -1 : 0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleBrowseClick();
          }
        }}
        role="button"
        aria-disabled={isDisabled}
        aria-label="Zone de glisser-déposer pour téléverser un PDF"
      >
        <UploadIcon className="mx-auto h-10 w-10 text-gray-400 mb-3" aria-hidden="true" />
        <p className="text-gray-600">
          <span className="font-medium">Cliquez pour parcourir</span> ou glissez-déposez
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Format accepté : PDF uniquement
        </p>
      </div>
      
      <input
        id="pdf-file"
        name="pdf-file"
        type="file"
        accept={acceptedFileTypes}
        className="sr-only"
        onChange={handleFileInputChange}
        ref={fileInputRef}
        disabled={isDisabled}
        aria-label="Sélectionner un fichier PDF"
      />
      
      <p className="text-sm text-gray-500" id="file-upload-help">
        Le fichier sera envoyé pour traitement, puis converti en format HTML accessible.
      </p>
    </div>
  );
};

export default FileUploader;