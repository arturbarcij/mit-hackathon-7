import { summarisePlot } from '../../src/engine/plot.ts'
import type { Label, LeafResult, PlotSummary } from '../../src/engine/types.ts'

export function emptyLeaf(label: Label | 'unsure', confidence = 0.9): LeafResult {
  const probs = { healthy: 0.02, rust: 0.02, cercospora: 0.02, phoma: 0.02, miner: 0.02, not_leaf: 0.02 }
  if (label !== 'unsure') probs[label] = confidence
  return {
    label,
    probs,
    confidence,
    quality: { ok: label !== 'unsure', blur: label === 'unsure' ? 1 : 80, brightness: 120 },
    abstained: label === 'unsure',
    modelVersion: 'mock',
  }
}

export function summaryOf(labels: Array<Label | 'unsure'>): PlotSummary {
  return summarisePlot(labels.map((label) => emptyLeaf(label)))
}
