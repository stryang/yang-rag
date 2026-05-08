import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      // Admin API (auth, users)
      '/api/v1/auth': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/users': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/runtime-settings': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/knowledge': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/system': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/vector-databases': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      // RAG API (knowledge bases)
      '/rag-api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/rag-api/, ''),
      },
    },
  },
})
