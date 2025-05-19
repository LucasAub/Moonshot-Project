import React from 'react';
import { Info } from 'lucide-react';

export const InfoBanner: React.FC = () => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8 text-blue-800">
      <div className="flex">
        <div className="flex-shrink-0">
          <Info className="h-5 w-5" aria-hidden="true" />
        </div>
        <div className="ml-3">
          <h2 className="text-sm font-medium">About This Tool</h2>
          <div className="mt-2 text-sm">
            <p>
              This tool helps convert PDF documents into accessible HTML format, making content more
              usable for screen readers and assistive technologies. The conversion process extracts text,
              preserves document structure, and enhances accessibility features.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};