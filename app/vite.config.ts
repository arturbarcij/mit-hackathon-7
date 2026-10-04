import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icon-192.png', 'icon-512.png'],
      manifest: {
        name: 'Jani',
        short_name: 'Jani',
        description: 'Coffee leaf check for the household phone. Works offline after install.',
        theme_color: '#145c32',
        background_color: '#f7f4ec',
        display: 'standalone',
        start_url: '/',
        lang: 'sw',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,json,woff2,onnx,wasm,mp3}'],
        maximumFileSizeToCacheInBytes: 15 * 1024 * 1024,
        navigateFallback: '/index.html',
      },
    }),
  ],
})
