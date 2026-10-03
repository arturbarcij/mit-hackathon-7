/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_USE_MOCK_MODEL?: string
  readonly VITE_SYNC_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'virtual:pwa-register' {
  export function registerSW(options?: { immediate?: boolean }): (reloadPage?: boolean) => Promise<void>
}
