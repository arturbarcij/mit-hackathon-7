import type { Lang } from './types.ts'

let current: HTMLAudioElement | null = null

/**
 * Play a pre-rendered clip. Falls back from the chosen language to Swahili,
 * then English. If no file exists, resolve without throwing so the text stands.
 * Returns true when a clip actually started.
 */
export async function play(answerId: string, lang: Lang): Promise<boolean> {
  stop()
  const order: Lang[] = lang === 'en' ? ['en', 'sw'] : lang === 'kik' ? ['kik', 'sw', 'en'] : ['sw', 'en']
  for (const code of order) {
    const started = await startClip(`/audio/${code}/${answerId}.mp3`)
    if (started) return true
  }
  return false
}

export function stop(): void {
  if (!current) return
  current.pause()
  current.src = ''
  current = null
}

function startClip(url: string): Promise<boolean> {
  return new Promise((resolve) => {
    const audio = new Audio(url)
    current = audio
    const finish = (ok: boolean) => {
      audio.removeEventListener('playing', onPlaying)
      audio.removeEventListener('error', onError)
      if (!ok && current === audio) current = null
      resolve(ok)
    }
    const onPlaying = () => finish(true)
    const onError = () => finish(false)
    audio.addEventListener('playing', onPlaying)
    audio.addEventListener('error', onError)
    void audio.play().catch(() => finish(false))
  })
}
