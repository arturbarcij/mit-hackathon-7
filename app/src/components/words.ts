import type { AnswerCard, Decision, Label, Lang, LeafResult, PlotSummary, QualityResult } from '../engine/types'

const LABEL_WORD: Record<Label, string> = {
  healthy: 'Healthy',
  rust: 'Rust',
  cercospora: 'Brown eye spot',
  phoma: 'Phoma',
  miner: 'Leaf miner',
  not_leaf: 'Not a leaf',
}

export function leafCaption(leaf: LeafResult): string {
  if (leaf.abstained || leaf.label === 'unsure') return 'Not sure'
  return LABEL_WORD[leaf.label]
}

export function leafKind(leaf: LeafResult): Label | 'unsure' {
  if (leaf.abstained || leaf.label === 'unsure') return 'unsure'
  return leaf.label
}

export function summarySentence(summary: PlotSummary): string {
  const parts: string[] = []
  const problems: Label[] = ['rust', 'cercospora', 'phoma', 'miner']
  for (const label of problems) {
    const count = summary.counts[label] ?? 0
    if (count > 0) {
      parts.push(`${count} of ${summary.n} leaves show ${LABEL_WORD[label].toLowerCase()}.`)
    }
  }
  const notLeaf = summary.counts.not_leaf ?? 0
  if (notLeaf > 0) {
    parts.push(`${notLeaf} of ${summary.n} leaves are not a leaf.`)
  }
  const healthy = summary.counts.healthy ?? 0
  if (parts.length === 0 && healthy > 0) {
    parts.push(`${healthy} of ${summary.n} leaves look healthy.`)
  }
  if (summary.uncertain > 0) {
    parts.push(`${summary.uncertain} not sure.`)
  }
  if (parts.length === 0) {
    parts.push('No leaves in this check.')
  }
  return parts.join(' ')
}

export function qualityLine(reason: QualityResult['reason']): string {
  if (reason === 'blurry') return 'Too blurry. Take the photo again.'
  if (reason === 'dark') return 'Too dark. Take the photo in daylight.'
  if (reason === 'too_small') return 'The leaf is too small. Move closer and take the photo again.'
  return 'This photo cannot be used. Take it again.'
}

export function decisionLine(decision: Decision | undefined): string {
  if (decision === 'act') return 'I will act'
  if (decision === 'wait') return 'I will wait'
  if (decision === 'ask') return 'Ask the officer'
  return 'No choice saved'
}

export function formatWhen(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function pickLang(map: Partial<Record<Lang, string>> | undefined, lang: Lang): string {
  if (!map) return ''
  const preferred = map[lang]?.trim()
  if (preferred) return preferred
  return map.en?.trim() ?? ''
}

export function cardText(card: AnswerCard, lang: Lang): string {
  return pickLang(card.text, lang)
}

export function cardNotSure(card: AnswerCard, lang: Lang): string {
  return pickLang(card.notSure, lang)
}
