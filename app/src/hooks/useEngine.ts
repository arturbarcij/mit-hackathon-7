import { useEffect, useState } from 'react'
import { getConsent, loadModel, setConsent, type ModelInfo } from '../engine/index.ts'

export function useOnline(): boolean {
  const [online, setOnline] = useState(() => (typeof navigator === 'undefined' ? true : navigator.onLine))
  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])
  return online
}

export function useModel(): ModelInfo {
  const [model, setModel] = useState<ModelInfo>({ version: 'mock', mock: true })
  useEffect(() => {
    void loadModel().then(setModel)
  }, [])
  return model
}

export function useConsent(): {
  consent: { main: boolean; photos: boolean } | null
  save: (next: { main: boolean; photos: boolean }) => Promise<void>
} {
  const [consent, setLocal] = useState<{ main: boolean; photos: boolean } | null>(null)
  useEffect(() => {
    void getConsent().then(setLocal)
  }, [])
  async function save(next: { main: boolean; photos: boolean }) {
    await setConsent(next)
    setLocal(next)
  }
  return { consent, save }
}

export function useEngine() {
  const online = useOnline()
  const model = useModel()
  return { online, model }
}
