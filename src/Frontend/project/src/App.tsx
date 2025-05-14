import React from 'react';
import PDFAccessibilityConverter from './components/PDFAccessibilityConverter';
import { AccessibilityProvider } from './context/AccessibilityContext';

function App() {
  return (
    <AccessibilityProvider>
      <div className="min-h-screen bg-white">
        <main id="main" role="main" className="container mx-auto px-4 py-8">
          <PDFAccessibilityConverter />
        </main>
      </div>
    </AccessibilityProvider>
  );
}

export default App;