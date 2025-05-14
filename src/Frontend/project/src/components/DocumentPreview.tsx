import React, { useRef, useEffect } from 'react';

interface DocumentPreviewProps {
  htmlContent: string;
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({ htmlContent }) => {
  const previewRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (previewRef.current) {
      previewRef.current.innerHTML = htmlContent;
      
      // Make all links in the preview accessible
      const links = previewRef.current.querySelectorAll('a');
      links.forEach(link => {
        if (!link.hasAttribute('aria-label')) {
          link.setAttribute('aria-label', `Lien: ${link.textContent}`);
        }
        link.setAttribute('tabindex', '0');
      });
    }
  }, [htmlContent]);

  return (
    <div className="mt-4">
      <h3 className="text-md font-medium mb-2" id="preview-heading">
        Aperçu du document converti:
      </h3>
      <div 
        className="p-4 border border-gray-200 rounded bg-white max-h-96 overflow-y-auto"
        ref={previewRef}
        tabIndex={0}
        aria-labelledby="preview-heading"
        role="region"
      />
      <p className="text-sm text-gray-500 mt-2">
        Cet aperçu est limité. Pour une expérience complète, téléchargez le document HTML.
      </p>
    </div>
  );
};

export default DocumentPreview;