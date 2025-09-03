import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/mode': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/screensaver_image': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
      },
    },
  },
})
