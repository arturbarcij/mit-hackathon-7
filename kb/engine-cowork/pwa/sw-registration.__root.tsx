import { HeadContent, Outlet, Scripts, createRootRoute } from '@tanstack/react-router'
import { useEffect } from 'react'
// Plain CSS import. A '?url' import produced a different hash in the SSR bundle than in the client
// bundle (tailwind output differs per environment), so the SSR HTML linked a stylesheet that 404s.
import '../styles.css'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { name: 'theme-color', content: '#2f6b3a' },
      { title: 'Jani' },
    ],
    links: [
      // vite-plugin-pwa cannot inject this because there is no index.html. Add it by hand.
      { rel: 'manifest', href: '/manifest.webmanifest' },
      { rel: 'icon', href: '/icons/icon-192.png' },
    ],
  }),
  shellComponent: RootDocument,
})

function RootDocument({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Manual service worker registration. `virtual:pwa-register` is provided by vite-plugin-pwa.
    // Dynamic import keeps it out of the SSR bundle. In dev (devOptions.enabled false) it is a no-op.
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return
    import('virtual:pwa-register')
      .then(({ registerSW }) => {
        registerSW({
          immediate: true,
          onOfflineReady() {
            console.log('[pwa] offline ready')
          },
          onRegisteredSW(url) {
            console.log('[pwa] registered', url)
          },
        })
      })
      .catch((e) => console.warn('[pwa] register failed', e))
  }, [])
  return (
    <html lang="sw">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-screen bg-white text-gray-900">
        {children}
        <Scripts />
      </body>
    </html>
  )
}

