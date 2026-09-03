import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/sourcing': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/outreach': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/cv-screening': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
