// Typed access to the content JSON written by the content-voice agent.
// Plain data imports only: safe under SSR (no browser globals).
import answersJson from '../content/answers.json';
import rulesJson from '../content/rules.json';
import seasonJson from '../content/season.json';
import type { AnswerEntry, Rule, SeasonFile } from './types';

export const ANSWERS: readonly AnswerEntry[] = answersJson as unknown as AnswerEntry[];
export const RULES: readonly Rule[] = rulesJson as unknown as Rule[];
export const SEASON: SeasonFile = seasonJson as unknown as SeasonFile;

const byId = new Map<string, AnswerEntry>(ANSWERS.map((a) => [a.id, a]));

/** Raw answers.json entry, or undefined when the id is unknown. */
export function answerById(id: string): AnswerEntry | undefined {
  return byId.get(id);
}
