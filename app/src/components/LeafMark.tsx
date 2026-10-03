import type { Label } from '../engine/types'

interface LeafMarkProps {
  kind: Label | 'unsure'
}

export function LeafMark({ kind }: LeafMarkProps) {
  if (kind === 'unsure') {
    return (
      <span className="unsure-mark" aria-hidden="true">
        ?
      </span>
    )
  }

  const common = {
    width: 40,
    height: 40,
    viewBox: '0 0 40 40',
    'aria-hidden': true as const,
    focusable: false as const,
  }

  if (kind === 'healthy') {
    return (
      <svg {...common}>
        <circle cx="20" cy="20" r="11" fill="none" stroke="#1a1a1a" strokeWidth="2" />
      </svg>
    )
  }

  if (kind === 'rust') {
    return (
      <svg {...common}>
        <circle cx="12" cy="14" r="3" fill="#1a1a1a" />
        <circle cx="22" cy="12" r="3" fill="#1a1a1a" />
        <circle cx="28" cy="22" r="3" fill="#1a1a1a" />
        <circle cx="16" cy="26" r="3" fill="#1a1a1a" />
      </svg>
    )
  }

  if (kind === 'cercospora') {
    return (
      <svg {...common}>
        <circle cx="20" cy="20" r="12" fill="none" stroke="#1a1a1a" strokeWidth="2" />
        <circle cx="20" cy="20" r="4" fill="none" stroke="#1a1a1a" strokeWidth="2" />
      </svg>
    )
  }

  if (kind === 'phoma') {
    return (
      <svg {...common}>
        <polygon points="20,6 34,33 6,33" fill="none" stroke="#1a1a1a" strokeWidth="2" />
      </svg>
    )
  }

  if (kind === 'miner') {
    return (
      <svg {...common}>
        <path
          d="M4 22 H12 L16 10 L22 30 L28 16 H36"
          fill="none"
          stroke="#1a1a1a"
          strokeWidth="2"
        />
      </svg>
    )
  }

  return (
    <svg {...common}>
      <rect x="8" y="8" width="24" height="24" fill="none" stroke="#1a1a1a" strokeWidth="2" />
      <path d="M12 12 L28 28 M28 12 L12 28" stroke="#1a1a1a" strokeWidth="2" />
    </svg>
  )
}
