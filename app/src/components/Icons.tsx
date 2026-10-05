type Kind = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf' | 'unsure' | 'none' | 'leaf' | 'speaker'

export function Mark({ kind }: { kind: Kind | string }) {
  return (
    <svg className={`mark mark-${kind}`} viewBox="0 0 48 48" aria-hidden="true">
      {shape(kind)}
    </svg>
  )
}

function shape(kind: string) {
  if (kind === 'speaker') {
    return (
      <>
        <path d="M8 18 h8 l10-8 v28 l-10-8 H8 z" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <path d="M32 18 a8 8 0 0 1 0 12" fill="none" stroke="currentColor" strokeWidth="2.5" />
      </>
    )
  }
  if (kind === 'not_leaf') {
    return (
      <>
        <rect x="8" y="8" width="32" height="32" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <path d="M16 16 L32 32 M32 16 L16 32" fill="none" stroke="currentColor" strokeWidth="2.5" />
      </>
    )
  }
  if (kind === 'unsure' || kind === 'none') {
    return (
      <>
        <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <text x="24" y="31" textAnchor="middle" fontSize="22" fill="currentColor" fontFamily="sans-serif">
          ?
        </text>
      </>
    )
  }
  if (kind === 'rust') {
    return (
      <>
        <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="16" cy="22" r="2.2" fill="currentColor" />
        <circle cx="24" cy="28" r="2.2" fill="currentColor" />
        <circle cx="30" cy="18" r="2.2" fill="currentColor" />
      </>
    )
  }
  if (kind === 'cercospora') {
    return (
      <>
        <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="24" cy="24" r="6" fill="none" stroke="currentColor" strokeWidth="2.5" />
      </>
    )
  }
  if (kind === 'phoma') {
    return <circle cx="24" cy="24" r="12" fill="currentColor" />
  }
  if (kind === 'miner') {
    return (
      <>
        <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <path d="M12 28 C18 18 22 30 28 20 C32 16 36 22 38 18" fill="none" stroke="currentColor" strokeWidth="2.5" />
      </>
    )
  }
  if (kind === 'healthy') {
    return (
      <>
        <circle cx="24" cy="24" r="16" fill="none" stroke="currentColor" strokeWidth="2.5" />
        <path d="M16 25 l6 6 12-14" fill="none" stroke="currentColor" strokeWidth="2.5" />
      </>
    )
  }
  return <path d="M24 6 C24 6 10 18 10 30 a14 14 0 0 0 28 0 C38 18 24 6 24 6 z" fill="none" stroke="currentColor" strokeWidth="2.5" />
}
