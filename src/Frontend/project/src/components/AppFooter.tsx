import React from 'react';

export const AppFooter: React.FC = () => {
  return (
    <footer className="bg-gray-800 text-gray-300 py-6 mt-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center mb-4">
          <p className="mb-2">This tool is for educational and demonstration purposes only.</p>
          <p>It helps convert PDF documents to more accessible HTML formats.</p>
        </div>
        
        <div className="text-center text-sm text-gray-400">
          <p>&copy; {new Date().getFullYear()} PDF to Accessible HTML Converter</p>
        </div>
      </div>
    </footer>
  );
};