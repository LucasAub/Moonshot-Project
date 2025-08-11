import { ConversionResult } from '../types/conversion';

/**
 * Sends a PDF file to the backend for conversion to HTML
 * @param file The PDF file to convert
 * @returns A promise with the conversion result
 */
export const convertPdfToHtml = async (file: File): Promise<ConversionResult> => {
  // Using Vite's proxied API endpoint
  const API_URL = '/api/convert';

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(API_URL, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = 'Failed to convert file';
      
      try {
        // Essayer de parser la réponse comme JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } else {
          // Si ce n'est pas du JSON, lire comme texte
          const textError = await response.text();
          errorMessage = textError || `Erreur HTTP ${response.status}`;
        }
      } catch (parseError) {
        // Si même la lecture en texte échoue
        errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
      }
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    
    // Si c'est une erreur de réseau ou de connexion
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Impossible de se connecter au serveur. Assurez-vous que le serveur backend fonctionne.');
    }
    
    throw error instanceof Error ? error : new Error('Failed to convert PDF');
  }
};