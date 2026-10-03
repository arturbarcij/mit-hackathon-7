export type Lang = 'sw' | 'kik' | 'en'

export type Label = 'healthy' | 'rust' | 'cercospora' | 'phoma' | 'miner' | 'not_leaf'

export const LABELS: Label[] = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf']

export const PROBLEM_LABELS: Label[] = ['rust', 'cercospora', 'phoma', 'miner']

export interface QualityResult {
  ok: boolean
  reason?: 'blurry' | 'dark' | 'too_small'
  blur: number
  brightness: number
}

export interface LeafResult {
  label: Label | 'unsure'
  probs: Record<Label, number>
  confidence: number
  quality: QualityResult
  abstained: boolean
  modelVersion: string
}

export interface PlotSummary {
  n: number
  counts: Record<Label, number>
  uncertain: number
  dominant: Label | 'none'
  affected: number
  distinctProblems: number
}

export type SeasonWindow = 'pre_short_rains' | 'short_rains' | 'pre_long_rains' | 'long_rains' | 'dry'

export interface AnswerCard {
  id: string
  severity: 'ok' | 'watch' | 'act' | 'ask'
  text: Partial<Record<Lang, string>>
  notSure?: Partial<Record<Lang, string>>
  audio: Partial<Record<Lang, string>>
  sources: string[]
  assumption: boolean
}

export type Decision = 'act' | 'wait' | 'ask'

export interface Check {
  id: string
  createdAt: string
  lang: Lang
  leaves: LeafResult[]
  summary: PlotSummary
  window: SeasonWindow
  answerId: string
  decision?: Decision
  memberId?: string
  plotId?: string
  consentMain: boolean
  consentPhotos: boolean
  synced: boolean
  synthetic: boolean
}

export interface ParsedReferral {
  memberId: string
  plotId: string
  date: string
  n: number
  rust: number
  cercospora: number
  phoma: number
  miner: number
  uncertain: number
  answerId: string
  confidence: number
  decision: Decision
}
