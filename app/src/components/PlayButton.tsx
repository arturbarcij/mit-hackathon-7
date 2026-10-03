import type { Lang } from '../engine/types'
import { play } from '../engine'

interface PlayButtonProps {
  answerId: string
  lang: Lang
  label?: string
}

export function PlayButton({ answerId, lang, label = 'Play' }: PlayButtonProps) {
  return (
    <button
      type="button"
      className="btn btn-quiet"
      onClick={() => {
        try {
          void Promise.resolve(play(answerId, lang)).catch(() => undefined)
        } catch {
          /* Missing audio stays on screen as text. */
        }
      }}
    >
      {label}
    </button>
  )
}
