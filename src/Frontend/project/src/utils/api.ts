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
      const error = await response.json();
      throw new Error(error.detail || 'Failed to convert file');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error instanceof Error ? error : new Error('Failed to convert PDF');
  }
};