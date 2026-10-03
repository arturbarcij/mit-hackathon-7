import { AppFrame } from '../components/AppFrame'
import { loadSourceItems } from '../components/optionalContent'

const LIMITS = [
  'Berries, including coffee berry disease.',
  'Nutrient problems.',
  'Roots.',
  'Varieties.',
  'Night photos.',
]

export default function SourcesPage() {
  const sources = loadSourceItems()

  return (
    <AppFrame>
      <h1>Limits and sources</h1>
      <h2>What this tool cannot see</h2>
      <ul className="list">
        {LIMITS.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <h2>Sources</h2>
      {sources.length === 0 ? (
        <p>The source list is not loaded.</p>
      ) : (
        <ul className="list">
          {sources.map((source) => (
            <li key={source.key}>
              {source.href ? (
                <a href={source.href} rel="noreferrer">
                  {source.label}
                </a>
              ) : (
                source.label
              )}
            </li>
          ))}
        </ul>
      )}
    </AppFrame>
  )
}
