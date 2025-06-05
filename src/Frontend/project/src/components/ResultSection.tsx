import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Download, Eye, EyeOff, ExternalLink } from 'lucide-react';

interface ResultSectionProps {
  htmlResult: string;
  documentTitle?: string;
}

export const ResultSection: React.FC<ResultSectionProps> = ({ 
  htmlResult, 
  documentTitle 
}) => {
  const [showPreview, setShowPreview] = useState(true);
  const previewRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (showPreview && previewRef.current) {
      previewRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [showPreview]);

  const handleDownload = () => {
    const blob = new Blob([htmlResult], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = documentTitle ? `${documentTitle.replace(/\s+/g, '-')}.html` : 'converted-document.html';
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const togglePreview = () => {
    setShowPreview(prev => !prev);
  };

  return (
    <motion.div
      className="mt-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          Conversion Complete
        </h2>
        
        {documentTitle && (
          <div className="mb-4 p-3 bg-gray-50 rounded border border-gray-200">
            <p className="text-gray-700">
              <strong>Document Title:</strong> {documentTitle}
            </p>
          </div>
        )}
        
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleDownload}
            className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg inline-flex items-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            aria-label="Download HTML file"
          >
            <Download className="mr-2" size={18} aria-hidden="true" />
            Download HTML
          </button>
          
          <button
            onClick={togglePreview}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-lg inline-flex items-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
            aria-expanded={showPreview}
            aria-controls="preview-pane"
          >
            {showPreview ? (
              <>
                <EyeOff className="mr-2" size={18} aria-hidden="true" />
                Hide Preview
              </>
            ) : (
              <>
                <Eye className="mr-2" size={18} aria-hidden="true" />
                Show Preview
              </>
            )}
          </button>
          
          {/* For a real application, we would have a way to open in a new tab */}
          <button
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-lg inline-flex items-center transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
            aria-label="Open in new tab"
          >
            <ExternalLink className="mr-2" size={18} aria-hidden="true" />
            Open in New Tab
          </button>
        </div>
      </div>
      
      {showPreview && (
        <div 
          id="preview-pane"
          ref={previewRef}
          className="border rounded-lg bg-white p-6 mt-4 mb-8 max-h-[500px] overflow-auto"
        >
          <h3 className="text-lg font-semibold mb-4 pb-2 border-b">HTML Preview</h3>
          <div 
            className="preview-content"
            dangerouslySetInnerHTML={{ 
              __html: htmlResult
                // Basic sanitization to prevent XSS
                .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                .replace(/on\w+="[^"]*"/g, '')
            }} 
          />
        </div>
      )}
    </motion.div>
  );
};