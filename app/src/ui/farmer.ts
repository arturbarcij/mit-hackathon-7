// What the farmer sees per leaf and per plot. Move 5: the farmer screens name only what the model
// can tell apart: rust, no problem seen, other spots (ask the officer), not sure.
// Cercospora, phoma and miner are never shown by name; they are counted as "other spots".
import type { Lang, LeafResult, PlotSummary } from '../engine';
import type { IconName } from '../components/Icon';
import { t } from './strings';

export type FarmerGroup = 'rust' | 'no_problem' | 'other_spots' | 'not_sure';

export const GROUPS: readonly FarmerGroup[] = ['rust', 'no_problem', 'other_spots', 'not_sure'];

export const GROUP_ICON: Record<FarmerGroup, IconName> = {
  rust: 'rust',
  no_problem: 'leaf',
  other_spots: 'spots',
  not_sure: 'question',
};

export function leafGroup(r: LeafResult): FarmerGroup {
  if (r.abstained || r.label === 'unsure' || r.label === 'not_leaf') return 'not_sure';
  if (r.label === 'rust') return 'rust';
  if (r.label === 'healthy') return 'no_problem';
  return 'other_spots';
}

export function groupCounts(s: PlotSummary): Record<FarmerGroup, number> {
  return {
    rust: s.counts.rust,
    no_problem: s.counts.healthy,
    other_spots: s.counts.cercospora + s.counts.phoma + s.counts.miner,
    not_sure: s.uncertain,
  };
}

export function groupLabel(g: FarmerGroup, lang: Lang): string {
  return t(g, lang);
}

/** One spoken line for the summary screen, built from the labels and counts on screen. */
export function summarySentence(s: PlotSummary, lang: Lang): string {
  const c = groupCounts(s);
  return GROUPS.map((g) => `${groupLabel(g, lang)}: ${c[g]}.`).join(' ');
}
