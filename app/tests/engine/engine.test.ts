import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { listAnswers, getRules } from '../../src/engine/content.ts'
import { decide } from '../../src/engine/decide.ts'
import { classifyRgba } from '../../src/engine/model.mock.ts'
import { summarisePlot } from '../../src/engine/plot.ts'
import { assessRgba } from '../../src/engine/quality.ts'
import { buildReferral, parseReferral } from '../../src/engine/referral.ts'
import { makeSample } from '../../src/engine/samples.ts'
import { seasonWindow } from '../../src/engine/season.ts'
import { emptyLeaf, summaryOf } from './helpers.ts'

const REQUIRED = [
  'how_to_pick_leaves',
  'how_to_photograph',
  'retake_blurry',
  'retake_dark',
  'not_a_leaf',
  'healthy_all',
  'rust_low',
  'rust_high_pre_rains',
  'rust_high_in_rains',
  'rust_high_dry',
  'cercospora',
  'phoma',
  'miner',
  'mixed_problems',
  'too_many_unsure',
  'ask_officer',
  'berries_out_of_scope',
  'other_crop',
  'consent_main',
  'consent_photos',
  'decision_act',
  'decision_wait',
  'decision_ask',
  'referral_ready',
  'language_name',
]

const KIKUYU = [
  'how_to_pick_leaves',
  'healthy_all',
  'rust_high_pre_rains',
  'too_many_unsure',
  'ask_officer',
  'decision_act',
  'decision_wait',
  'decision_ask',
]

describe('answer bank and rules', () => {
  it('has every required line in English and Swahili', () => {
    const answers = listAnswers()
    const ids = new Set(answers.map((item) => item.id))
    for (const id of REQUIRED) {
      expect(ids.has(id), id).toBe(true)
      const row = answers.find((item) => item.id === id)
      expect(row?.text.en, id).toBeTruthy()
      expect(row?.text.sw, id).toBeTruthy()
    }
    for (const id of KIKUYU) {
      expect(answers.find((item) => item.id === id)?.text.kik, id).toBeTruthy()
    }
  })

  it('resolves every rule, and the last rule asks the officer', () => {
    const rules = getRules()
    const ids = new Set(listAnswers().map((item) => item.id))
    expect(rules.at(-1)?.then).toBe('ask_officer')
    expect(rules.at(-1)?.if).toEqual({})
    for (const rule of rules) expect(ids.has(rule.then)).toBe(true)
  })

  it('does not invent a dose or use an em dash', () => {
    const blob = JSON.stringify(listAnswers())
    expect(blob).not.toMatch(/\d+\s*(ml|mg|kg|g\/l)\b/i)
    expect(blob).not.toContain('—')
    expect(blob).not.toContain('–')
  })
})

describe('season window', () => {
  it('puts early October in the pre-short-rains decision', () => {
    expect(seasonWindow(new Date(2026, 9, 3))).toBe('pre_short_rains')
    expect(seasonWindow(new Date(2026, 9, 20))).toBe('pre_short_rains')
    expect(seasonWindow(new Date(2026, 10, 10))).toBe('short_rains')
    expect(seasonWindow(new Date(2026, 6, 15))).toBe('dry')
    expect(seasonWindow(new Date(2026, 1, 25))).toBe('pre_long_rains')
    expect(seasonWindow(new Date(2026, 2, 20))).toBe('long_rains')
  })
})

describe('plot and decision', () => {
  it('keeps unsure leaves out of the class counts', () => {
    const leaves = [
      ...Array.from({ length: 6 }, () => emptyLeaf('rust')),
      ...Array.from({ length: 3 }, () => emptyLeaf('healthy')),
      emptyLeaf('unsure'),
    ]
    const summary = summarisePlot(leaves)
    expect(summary.affected).toBe(6)
    expect(summary.uncertain).toBe(1)
    expect(summary.counts.rust).toBe(6)
    expect(summary.dominant).toBe('rust')
  })

  it('selects the October rust card for the synthetic demo plot', () => {
    const summary = summaryOf([
      ...Array.from({ length: 6 }, () => 'rust' as const),
      ...Array.from({ length: 3 }, () => 'healthy' as const),
      'unsure' as const,
    ])
    const card = decide(summary, new Date(2026, 9, 4))
    expect(card.id).toBe('rust_high_pre_rains')
    expect(card.assumption).toBe(true)
  })

  it('asks the officer when leaves disagree or are unclear', () => {
    expect(decide(summaryOf(['rust', 'rust', 'miner', 'miner', 'healthy']), new Date(2026, 9, 4)).id).toBe('mixed_problems')
    expect(decide(summaryOf(['unsure', 'unsure', 'unsure', 'healthy']), new Date(2026, 9, 4)).id).toBe('too_many_unsure')
    expect(decide(summaryOf(['healthy', 'healthy']), new Date(2026, 9, 4)).id).toBe('healthy_all')
    expect(decide(summaryOf(['not_leaf', 'not_leaf']), new Date(2026, 9, 4)).id).toBe('not_a_leaf')
    const odd = summarisePlot([])
    odd.dominant = 'healthy'
    odd.affected = 2
    expect(decide(odd, new Date(2026, 9, 4)).id).toBe('ask_officer')
  })
})

describe('quality gate and mock labels', () => {
  it('rejects dark, blurred and tiny pictures', () => {
    const dark = makeSample('dark')
    const blur = makeSample('blur')
    const tiny = { width: 32, height: 32, rgba: new Uint8ClampedArray(32 * 32 * 4).fill(180) }
    expect(assessRgba(dark.width, dark.height, dark.rgba).reason).toBe('dark')
    expect(assessRgba(blur.width, blur.height, blur.rgba).reason).toBe('blurry')
    expect(assessRgba(tiny.width, tiny.height, tiny.rgba).reason).toBe('too_small')
    const healthy = makeSample('healthy')
    expect(assessRgba(healthy.width, healthy.height, healthy.rgba).ok).toBe(true)
  })

  it('reads the sample name and abstains when the photo fails', () => {
    const rust = makeSample('rust')
    const named = classifyRgba(rust.width, rust.height, rust.rgba, 'rust')
    expect(named.label).toBe('rust')
    expect(named.abstained).toBe(false)
    const blur = makeSample('blur')
    const failed = classifyRgba(blur.width, blur.height, blur.rgba, 'rust')
    expect(failed.abstained).toBe(true)
    expect(failed.label).toBe('unsure')
  })
})

describe('referral SMS', () => {
  it('stays within 160 characters and round-trips', () => {
    const summary = summaryOf([
      ...Array.from({ length: 6 }, () => 'rust' as const),
      'miner' as const,
      'unsure' as const,
      'healthy' as const,
      'healthy' as const,
    ])
    const text = buildReferral({
      id: 'c1',
      createdAt: '2026-10-04T09:00:00',
      lang: 'sw',
      leaves: [emptyLeaf('rust', 0.87)],
      summary,
      window: 'pre_short_rains',
      answerId: 'rust_high_pre_rains',
      decision: 'ask',
      memberId: 'OCC0412',
      plotId: '2',
      consentMain: true,
      consentPhotos: false,
      synced: false,
      synthetic: true,
    })
    expect(text.length).toBeLessThanOrEqual(160)
    expect(text.startsWith('JANI1 ')).toBe(true)
    const parsed = parseReferral(text)
    expect(parsed?.memberId).toBe('OCC0412')
    expect(parsed?.rust).toBe(6)
    expect(parsed?.miner).toBe(1)
    expect(parsed?.uncertain).toBe(1)
    expect(parsed?.answerId).toBe('rust_high_pre_rains')
    expect(parsed?.decision).toBe('ask')
    expect(parseReferral('hello')).toBeNull()
  })

  it('parses the contract example', () => {
    const parsed = parseReferral(
      'JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask',
    )
    expect(parsed?.confidence).toBe(87)
    expect(parsed?.n).toBe(10)
  })
})

describe('client safety', () => {
  it('has no runtime AI API calls in the client', () => {
    const root = join(import.meta.dirname, '../../src')
    const files = walk(root)
    const banned = ['openai', 'anthropic', 'generativelanguage', 'elevenlabs', 'api.groq']
    for (const file of files) {
      const text = readFileSync(file, 'utf8').toLowerCase()
      for (const word of banned) expect(text.includes(word), `${file} ${word}`).toBe(false)
    }
  })
})

function walk(dir: string): string[] {
  const out: string[] = []
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) out.push(...walk(path))
    else if (/\.(ts|tsx|json)$/.test(name)) out.push(path)
  }
  return out
}
