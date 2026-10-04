import en from './content/i18n/en.json' with { type: 'json' }
import sw from './content/i18n/sw.json' with { type: 'json' }
import kik from './content/i18n/kik.json' with { type: 'json' }
import type { Lang } from './engine/types.ts'

const tables: Record<Lang, Record<string, string>> = {
  en: en as Record<string, string>,
  sw: sw as Record<string, string>,
  kik: kik as Record<string, string>,
}

export function t(lang: Lang, key: string, vars?: Record<string, string | number>): string {
  const raw = tables[lang][key] || tables.sw[key] || tables.en[key] || key
  if (!vars) return raw
  return raw.replace(/\{\{(\w+)\}\}/g, (_match, name: string) => String(vars[name] ?? ''))
}

export function labelKey(label: string): string {
  if (label === 'unsure' || label === 'none') return 'label_unsure'
  return `label_${label}`
}
