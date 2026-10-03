import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  resolve: {
    // Load the external WASM build. The bundled build pulls in a 28 MB JSEP file.
    conditions: ['onnxruntime-web-use-extern-wasm'],
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Jani',
        short_name: 'Jani',
        display: 'standalone',
        background_color: '#f4f1e8',
        theme_color: '#1f3d2b',
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,json,onnx,wasm,mp3}'],
        maximumFileSizeToCacheInBytes: 15 * 1024 * 1024,
      },
    }),
  ],
})
