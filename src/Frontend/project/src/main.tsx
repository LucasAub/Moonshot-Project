import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Add a skip to main content link for keyboard users
const skipLink = document.createElement('a');
skipLink.href = '#main';
skipLink.className = 'skip-to-content';
skipLink.textContent = 'Passer au contenu principal';
document.body.prepend(skipLink);

// Change page title to match application purpose
document.title = 'Convertisseur PDF Accessible';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);