import { useEffect, useState } from 'react'
import type { Lang } from '../engine/types'
import { loadModel } from '../engine'
import { useOnline } from '../hooks/useEngine'
import { ui } from './optionalContent'

function onlineNow(value: boolean | { online: boolean }): boolean {
  if (typeof value === 'boolean') return value
  return value.online
}

export function StatusBar({ lang = 'en' }: { lang?: Lang | null }) {
  const copyLang: Lang = lang ?? 'en'
  const online = onlineNow(useOnline())
  const [mock, setMock] = useState(false)

  useEffect(() => {
    let active = true
    loadModel()
      .then((model) => {
        if (active) setMock(Boolean(model.mock))
      })
      .catch(() => {
        if (active) setMock(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="status" role="status">
      <span className="badge">{online ? ui(copyLang, 'online', 'Online') : ui(copyLang, 'offline', 'Offline')}</span>
      {mock ? <span className="badge">Mock model</span> : null}
    </div>
  )
}
