import placeholderAnswers from './placeholders/answers.json';
import placeholderRules from './placeholders/rules.json';
import placeholderSeason from './placeholders/season.json';

/*
 * The content-voice agent owns src/content/{answers,rules,season}.json. Until a file lands there
 * the engine falls back to the placeholders in ./placeholders. The glob returns an empty object
 * when a file is missing, so the build never breaks on absent content.
 */
const answersFiles = import.meta.glob('../content/answers.json', { eager: true, import: 'default' });
const rulesFiles = import.meta.glob('../content/rules.json', { eager: true, import: 'default' });
const seasonFiles = import.meta.glob('../content/season.json', { eager: true, import: 'default' });

export interface ContentBundle {
  answers: unknown;
  rules: unknown;
  season: unknown;
  usingPlaceholders: { answers: boolean; rules: boolean; season: boolean };
}

function pick(files: Record<string, unknown>, fallback: unknown): { value: unknown; placeholder: boolean } {
  const first = Object.values(files)[0];
  return first === undefined ? { value: fallback, placeholder: true } : { value: first, placeholder: false };
}

export function loadContent(): ContentBundle {
  const a = pick(answersFiles, placeholderAnswers);
  const r = pick(rulesFiles, placeholderRules);
  const s = pick(seasonFiles, placeholderSeason);
  return {
    answers: a.value,
    rules: r.value,
    season: s.value,
    usingPlaceholders: { answers: a.placeholder, rules: r.placeholder, season: s.placeholder },
  };
}
