import React from 'react';
import { motion } from 'framer-motion';
import { FileUpload } from './components/FileUpload';
import { StatusBanner } from './components/StatusBanner';
import { ResultSection } from './components/ResultSection';
import { InfoBanner } from './components/InfoBanner';
import { AppHeader } from './components/AppHeader';
import { AppFooter } from './components/AppFooter';
import { useConversionProcess } from './hooks/useConversionProcess';

function App() {
  const {
    file,
    status,
    htmlResult,
    documentTitle,
    errorMessage,
    handleFileChange,
    handleConversion,
    resetConversion,
  } = useConversionProcess();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white p-3 rounded">
        Skip to main content
      </a>

      <AppHeader />

      <main id="main-content" className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-gray-800 mb-4 sm:text-4xl text-center">
            PDF to Accessible HTML Converter
          </h1>
          
          <InfoBanner />

          <FileUpload 
            file={file} 
            onFileChange={handleFileChange} 
            onConvert={handleConversion}
            isProcessing={status === 'processing'}
            disabled={status === 'processing'}
          />

          {status !== 'idle' && (
            <StatusBanner 
              status={status} 
              errorMessage={errorMessage}
              onReset={resetConversion}
            />
          )}

          {status === 'success' && htmlResult && (
            <ResultSection 
              htmlResult={htmlResult} 
              documentTitle={documentTitle} 
            />
          )}
        </motion.div>
      </main>

      <AppFooter />
    </div>
  );
}

export default App;