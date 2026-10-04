// Service worker registration for the static PWA (UI-side; the engine does not register one yet).
// offlineStatus() resolves ready: true only once a worker is active, which only happens after its
// install step cached every file in the precache list.
export interface OfflineStatus {
  ready: boolean;
  version?: string;
  files?: number;
  bytes?: number;
}

let started: Promise<OfflineStatus> | null = null;

function allowed(): boolean {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return false;
  if (!import.meta.env.PROD) return false;
  return true;
}

function askStatus(sw: ServiceWorker): Promise<OfflineStatus> {
  return new Promise((resolve) => {
    const ch = new MessageChannel();
    const timer = setTimeout(() => resolve({ ready: true }), 2000);
    ch.port1.onmessage = (e) => {
      clearTimeout(timer);
      resolve({ ready: true, version: e.data?.version, files: e.data?.files, bytes: e.data?.bytes });
    };
    sw.postMessage({ type: 'jani-status' }, [ch.port2]);
  });
}

export function registerOffline(): Promise<OfflineStatus> {
  if (started) return started;
  if (!allowed()) return (started = Promise.resolve({ ready: false }));
  started = (async () => {
    try {
      const base = import.meta.env.BASE_URL;
      await navigator.serviceWorker.register(`${base}sw.js`, { scope: base, updateViaCache: 'none' });
      const reg = await navigator.serviceWorker.ready;
      const status = reg.active ? await askStatus(reg.active) : { ready: false };
      (window as unknown as { __janiOffline?: OfflineStatus }).__janiOffline = status;
      return status;
    } catch {
      return { ready: false };
    }
  })();
  return started;
}
