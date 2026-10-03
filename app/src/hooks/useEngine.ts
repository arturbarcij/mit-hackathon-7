import { useCallback, useEffect, useState } from 'react';
import {
  checkQuality,
  classifyLeaf,
  decide,
  getConsent,
  listChecks,
  loadModel,
  play,
  saveCheck,
  seasonWindow,
  setConsent,
  summarisePlot,
  syncPending,
} from '../engine/index.ts';
import type { Check } from '../engine/types.ts';

export function useOnline(): boolean {
  const [online, setOnline] = useState(() => {
    if (typeof navigator === 'undefined' || typeof navigator.onLine !== 'boolean') return true;
    return navigator.onLine;
  });
  useEffect(() => {
    if (typeof window === 'undefined' || typeof navigator === 'undefined' || typeof navigator.onLine !== 'boolean') {
      return;
    }
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    update();
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, []);
  return online;
}

export function useConsent() {
  const [consent, setLocal] = useState({ main: false, photos: false });
  useEffect(() => {
    let live = true;
    getConsent()
      .then((value) => {
        if (live) setLocal(value);
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, []);
  const update = useCallback(async (value: { main: boolean; photos: boolean }) => {
    await setConsent(value);
    setLocal(value);
  }, []);
  return { consent, setConsent: update };
}

export function useCheck() {
  const [checks, setChecks] = useState<Check[]>([]);
  const refresh = useCallback(async () => {
    setChecks(await listChecks());
  }, []);
  useEffect(() => {
    let live = true;
    listChecks()
      .then((rows) => {
        if (live) setChecks(rows);
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, []);
  const save = useCallback(async (check: Check) => {
    await saveCheck(check);
    setChecks(await listChecks());
  }, []);
  return { checks, saveCheck: save, refresh };
}

export function useEngine() {
  const [model, setModel] = useState<{ version: string; mock: boolean } | null>(null);
  useEffect(() => {
    let live = true;
    loadModel()
      .then((loaded) => {
        if (live) setModel(loaded);
      })
      .catch(() => {
        if (live) setModel({ version: 'mock', mock: true });
      });
    return () => {
      live = false;
    };
  }, []);
  return {
    model,
    loadModel,
    classifyLeaf,
    checkQuality,
    summarisePlot,
    seasonWindow,
    decide,
    play,
    syncPending,
  };
}
