import type { Lang } from '../engine/types'

const contentFiles: Record<string, unknown> = import.meta.glob('../content/**/*.json', {
  eager: true,
  import: 'default',
})

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>
  }
  return null
}

function readModule(suffix: string): unknown {
  for (const [path, value] of Object.entries(contentFiles)) {
    if (path.endsWith(suffix)) return value
  }
  return undefined
}

function lookupString(raw: unknown, key: string): string | null {
  const record = asRecord(raw)
  if (!record) return null
  const value = record[key]
  if (typeof value === 'string' && value.trim()) return value
  return null
}

export function t(lang: Lang, key: string, fallback: string): string {
  const preferred = lookupString(readModule(`/i18n/${lang}.json`), key)
  if (preferred) return preferred
  if (lang !== 'en') {
    const english = lookupString(readModule('/i18n/en.json'), key)
    if (english) return english
  }
  return fallback
}

export function ui(lang: Lang, key: string, english: string): string {
  if (lang !== 'sw') return english
  return t('sw', key, english)
}

function textFor(entry: Record<string, unknown>, lang: Lang): string | null {
  const text = asRecord(entry.text)
  if (!text) return null
  const preferred = text[lang]
  if (typeof preferred === 'string' && preferred.trim()) return preferred
  const english = text.en
  if (typeof english === 'string' && english.trim()) return english
  return null
}

function findAnswer(raw: unknown, id: string): Record<string, unknown> | null {
  if (Array.isArray(raw)) {
    for (const item of raw) {
      const record = asRecord(item)
      if (record && record.id === id) return record
    }
    return null
  }
  const record = asRecord(raw)
  if (!record) return null
  if (Array.isArray(record.answers)) return findAnswer(record.answers, id)
  const direct = asRecord(record[id])
  if (direct) return direct
  return null
}

export function answerLine(id: string, lang: Lang): string | null {
  const entry = findAnswer(readModule('/answers.json'), id)
  if (!entry) return null
  return textFor(entry, lang)
}

export interface SourceItem {
  key: string
  label: string
  href?: string
}

function pickString(record: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const value = record[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

function sourceList(raw: unknown): unknown[] {
  if (Array.isArray(raw)) return raw
  const record = asRecord(raw)
  if (!record) return []
  for (const key of ['sources', 'items', 'references']) {
    const value = record[key]
    if (Array.isArray(value)) return value
  }
  return []
}

export function loadSourceItems(): SourceItem[] {
  const items: SourceItem[] = []
  sourceList(readModule('/sources.json')).forEach((entry, index) => {
    if (typeof entry === 'string' && entry.trim()) {
      items.push({ key: `source-${index}`, label: entry.trim() })
      return
    }
    const record = asRecord(entry)
    if (!record) return
    const label = pickString(record, ['title', 'name', 'label', 'citation', 'id', 'text'])
    const href = pickString(record, ['url', 'href', 'link'])
    const year = record.year
    const yearSuffix = typeof year === 'number' || typeof year === 'string' ? ` (${year})` : ''
    const safeHref = href.startsWith('https://') || href.startsWith('http://') ? href : undefined
    if (!label && !safeHref) return
    items.push({
      key: `source-${index}-${label || href}`,
      label: `${label || href}${yearSuffix}`,
      href: safeHref,
    })
  })
  return items
}
