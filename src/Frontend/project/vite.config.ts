import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Remove optimizeDeps exclusion to ensure proper dependency handling
  server: {
    open: true, // Open browser on server start
    port: 5173  // Use a specific port
  }
});
