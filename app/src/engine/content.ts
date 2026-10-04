import answersFile from '../content/answers.json' with { type: 'json' }
import rulesFile from '../content/rules.json' with { type: 'json' }
import type { AnswerCard, Lang } from './types.ts'

export interface AnswerRecord {
  id: string
  kind: string
  severity: 'ok' | 'watch' | 'act' | 'ask'
  text: Partial<Record<Lang, string>>
  not_sure?: Partial<Record<Lang, string>>
  sources: string[]
  assumption: boolean
  translation_status?: Partial<Record<Lang, string>>
  reviewed_by: string | null
}

export interface RuleIf {
  dominant?: string
  affected_gte?: number
  affected_lte?: number
  uncertain_gte?: number
  distinct_problems_gte?: number
  window?: string
}

export interface Rule {
  if: RuleIf
  then: string
  assumption?: boolean
  note?: string
}

const answers = answersFile as Record<string, AnswerRecord>
const rules = rulesFile as Rule[]

export function getAnswer(id: string): AnswerRecord | undefined {
  return answers[id]
}

export function listAnswers(): AnswerRecord[] {
  return Object.values(answers)
}

export function getRules(): Rule[] {
  return rules
}

export function textFor(record: { text: Partial<Record<Lang, string>> }, lang: Lang): string {
  return record.text[lang] || record.text.sw || record.text.en || ''
}

export function toCard(record: AnswerRecord, assumption: boolean): AnswerCard {
  const audio: Partial<Record<Lang, string>> = {
    sw: `/audio/sw/${record.id}.mp3`,
    en: `/audio/en/${record.id}.mp3`,
  }
  if (record.text.kik) audio.kik = `/audio/kik/${record.id}.mp3`
  return {
    id: record.id,
    severity: record.severity,
    text: record.text,
    notSure: record.not_sure,
    audio,
    sources: record.sources,
    assumption: assumption || record.assumption,
  }
}
