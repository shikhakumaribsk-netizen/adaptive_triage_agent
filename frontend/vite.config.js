import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Fast Refresh is enabled by default in dev mode
      fastRefresh: true,
    }),
  ],

  resolve: {
    alias: {
      // allows: import Foo from '@/components/Foo'
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    host: true,          // expose on LAN so teammates can test on mobile
    open: true,          // auto-open browser on npm run dev
    proxy: {
      // Proxy /api calls to FastAPI backend during development
      // This avoids CORS issues when running locally
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,          // set true if you want source maps in prod
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // Split vendor libraries into separate chunks for better caching
        manualChunks: {
          react:    ['react', 'react-dom'],
        },
      },
    },
  },

  preview: {
    port: 4173,
    host: true,
  },

  // Environment variable prefix — only VITE_ vars are exposed to the browser
  envPrefix: 'VITE_',
});