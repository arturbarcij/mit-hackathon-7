export function PickFigure() {
  const leaves = [8, 24, 40, 56, 72, 16, 32, 48, 64, 80]
  return (
    <svg className="figure" viewBox="0 0 160 96" role="img" aria-label="Ten leaves on a plain page">
      <rect x="18" y="8" width="124" height="80" fill="#ffffff" stroke="#1a1a1a" strokeWidth="2" />
      {leaves.map((x, index) => (
        <ellipse
          key={x}
          cx={38 + (index % 5) * 22}
          cy={index < 5 ? 36 : 62}
          rx="8"
          ry="12"
          fill="none"
          stroke="#1a1a1a"
          strokeWidth="2"
        />
      ))}
    </svg>
  )
}
