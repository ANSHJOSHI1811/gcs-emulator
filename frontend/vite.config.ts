import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/compute': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/storage': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/upload': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/download': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/vpc': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/iam': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/monitoring': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/pubsub': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/run': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/gke': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/secretmanager': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/artifacts': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
})
