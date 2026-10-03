import { assessRgba } from './quality.ts'
import { LABELS, type Label, type LeafResult, type QualityResult } from './types.ts'

/** Below this calibrated probability the leaf is "not sure". */
export const ABSTAIN_BELOW = 0.6

const HINTS: Array<[string, Label]> = [
  ['not_leaf', 'not_leaf'],
  ['notleaf', 'not_leaf'],
  ['cercospora', 'cercospora'],
  ['phoma', 'phoma'],
  ['miner', 'miner'],
  ['rust', 'rust'],
  ['healthy', 'healthy'],
]

let pendingHint = ''

export function setMockHint(name: string): void {
  pendingHint = name.toLowerCase()
}

export function consumeMockHint(): string {
  const hint = pendingHint
  pendingHint = ''
  return hint
}

export function classifyRgba(
  width: number,
  height: number,
  rgba: Uint8ClampedArray,
  hint: string,
  quality?: QualityResult,
): LeafResult {
  const gate = quality ?? assessRgba(width, height, rgba)
  if (!gate.ok) return unsure(gate, colourProbs(width, height, rgba))

  const fromName = labelFromHint(hint)
  if (fromName) return sure(fromName, 0.9, gate)

  const guessed = guessColour(width, height, rgba)
  if (guessed.confidence < ABSTAIN_BELOW) return unsure(gate, guessed.probs)
  return {
    label: guessed.label,
    probs: guessed.probs,
    confidence: guessed.confidence,
    quality: gate,
    abstained: false,
    modelVersion: 'mock',
  }
}

function labelFromHint(hint: string): Label | null {
  for (const [needle, label] of HINTS) {
    if (hint.includes(needle)) return label
  }
  return null
}

function sure(label: Label, confidence: number, quality: QualityResult): LeafResult {
  const rest = (1 - confidence) / (LABELS.length - 1)
  const probs = emptyProbs()
  for (const key of LABELS) probs[key] = rest
  probs[label] = confidence
  return {
    label,
    probs,
    confidence,
    quality,
    abstained: confidence < ABSTAIN_BELOW,
    modelVersion: 'mock',
  }
}

function unsure(quality: QualityResult, probs: Record<Label, number>): LeafResult {
  const confidence = Math.max(...LABELS.map((label) => probs[label]))
  return {
    label: 'unsure',
    probs,
    confidence,
    quality,
    abstained: true,
    modelVersion: 'mock',
  }
}

function guessColour(
  width: number,
  height: number,
  rgba: Uint8ClampedArray,
): { label: Label; confidence: number; probs: Record<Label, number> } {
  let orange = 0
  let green = 0
  let brown = 0
  let blue = 0
  let n = 0
  const step = Math.max(1, Math.floor((width * height) / 4000))
  for (let p = 0; p < width * height; p += step) {
    const i = p * 4
    const r = rgba[i] ?? 0
    const g = rgba[i + 1] ?? 0
    const b = rgba[i + 2] ?? 0
    n++
    if (r > 150 && r > g + 20 && g > 50 && g < 190 && r > b + 20) orange++
    else if (g > r + 15 && g > b && g > 50) green++
    else if (r > 90 && g > 50 && b < 90 && r > b && Math.abs(r - g) < 80) brown++
    else if (b > r + 20 && b > g) blue++
  }
  const probs = emptyProbs()
  if (!n) return { label: 'healthy', confidence: 0.2, probs }
  const orangeShare = orange / n
  const greenShare = green / n
  const blueShare = blue / n
  const brownShare = brown / n
  if (blueShare > 0.45 && blueShare > greenShare) {
    fill(probs, 'not_leaf', 0.8)
    return { label: 'not_leaf', confidence: 0.8, probs }
  }
  if (orangeShare > 0.06 && orangeShare > brownShare) {
    fill(probs, 'rust', 0.78)
    return { label: 'rust', confidence: 0.78, probs }
  }
  if (greenShare > 0.55 && orangeShare < 0.04) {
    fill(probs, 'healthy', 0.8)
    return { label: 'healthy', confidence: 0.8, probs }
  }
  fill(probs, 'healthy', 0.34)
  return { label: 'healthy', confidence: 0.34, probs }
}

function colourProbs(width: number, height: number, rgba: Uint8ClampedArray): Record<Label, number> {
  return guessColour(width, height, rgba).probs
}

function emptyProbs(): Record<Label, number> {
  return { healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 }
}

function fill(probs: Record<Label, number>, label: Label, confidence: number): void {
  const rest = (1 - confidence) / (LABELS.length - 1)
  for (const key of LABELS) probs[key] = rest
  probs[label] = confidence
}
