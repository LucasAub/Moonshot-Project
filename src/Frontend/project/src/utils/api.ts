import { ConversionResult } from '../types/conversion';

/**
 * Sends a PDF file to the backend for conversion to HTML
 * @param file The PDF file to convert
 * @returns A promise with the conversion result
 */
export const convertPdfToHtml = async (file: File): Promise<ConversionResult> => {
  // For development/demo purposes, we'll simulate the API call
  // In a real application, this would be an actual API call to the backend
  
  // Mock API endpoint would be something like:
  // const API_URL = 'http://localhost:5000/convert' or from env variable

  // Simulate API call with a delay
  return new Promise((resolve, reject) => {
    // Simulating a network request
    setTimeout(() => {
      try {
        // This is a mock response. In a real app, we would send the file to the backend
        // const formData = new FormData();
        // formData.append('file', file);
        // const response = await fetch(API_URL, {
        //   method: 'POST',
        //   body: formData,
        // });
        // if (!response.ok) throw new Error('Failed to convert file');
        // const data = await response.json();
        // return data;
        
        // For simplicity in this mock, we'll extract the filename as the "title"
        const fileName = file.name.replace('.pdf', '');
        
        // Mock successful response
        if (Math.random() > 0.1) { // 90% success rate for demo
          resolve({
            html: `
              <!DOCTYPE html>
              <html lang="en">
              <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${fileName}</title>
              </head>
              <body>
                <header>
                  <h1>${fileName}</h1>
                </header>
                <main>
                  <article>
                    <section>
                      <h2>Introduction</h2>
                      <p>This is a sample converted HTML from the PDF document "${file.name}".</p>
                      <p>In a real application, this would contain the actual content extracted from your PDF.</p>
                    </section>
                    <section>
                      <h2>Content Section</h2>
                      <p>The purpose of this conversion is to make PDF content more accessible.</p>
                      <ul>
                        <li>Proper heading structure</li>
                        <li>Alt text for images</li>
                        <li>Semantic HTML elements</li>
                        <li>Accessible tables (when present)</li>
                      </ul>
                    </section>
                  </article>
                </main>
                <footer>
                  <p>Converted from PDF to HTML for improved accessibility</p>
                </footer>
              </body>
              </html>
            `,
            title: fileName,
            accessibilityScore: 92,
          });
        } else {
          // Simulate occasional errors
          reject(new Error('Could not process this PDF. It may be corrupted or password-protected.'));
        }
      } catch (error) {
        reject(error);
      }
    }, 2000); // Simulate 2 second processing time
  });
};