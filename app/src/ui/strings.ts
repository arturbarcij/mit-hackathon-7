// Short UI labels (button words, tile words). Every instruction sentence comes from
// answers.json through the engine; only these few labels live here.
// Swahili labels are a builder draft, not reviewed by a native speaker (see README_DEPLOY.md).
// Kikuyu labels are not written yet: Kikuyu falls back to Swahili and the screen shows the
// "not translated yet" tag.
import { getAnswer, type AnswerCard, type Lang, type SeasonWindow } from '../engine';

export const LANGS: readonly Lang[] = ['sw', 'kik', 'en'];

type Key =
  | 'next'
  | 'yes'
  | 'no'
  | 'take_photo'
  | 'upload'
  | 'sample'
  | 'retake'
  | 'skip'
  | 'done'
  | 'of'
  | 'leaves'
  | 'rust'
  | 'no_problem'
  | 'other_spots'
  | 'not_sure'
  | 'act'
  | 'wait'
  | 'ask'
  | 'send_sms'
  | 'history'
  | 'new_check'
  | 'start_again'
  | 'mock'
  | 'offline_ready'
  | 'offline_not_ready'
  | 'not_translated'
  | 'machine_draft'
  | 'draft'
  | 'model_missing'
  | 'photos_ok'
  | 'to_retake'
  | 'checking'
  | 'chars'
  | 'demo_number'
  | 'assumption'
  | 'sources'
  | 'no_checks'
  | 'credits'
  | 'sample_note'
  | 'back'
  | 'my_farm'
  | 'which_block'
  | 'tap_block'
  | 'coffee'
  | 'maize'
  | 'beans'
  | 'home'
  | 'upper_slope'
  | 'coffee_only'
  | 'check_block'
  | 'check_next'
  | 'status_ok'
  | 'status_watch'
  | 'status_act'
  | 'status_ask'
  | 'status_none'
  | 'overdue'
  | 'last_check'
  | 'days_ago'
  | 'day_ago'
  | 'today'
  | 'check_again_by'
  | 'example'
  | 'hide_example'
  | 'example_note'
  | 'schematic_note'
  | 'unassigned'
  | 'now_window'
  | 'win_pre_short_rains'
  | 'win_short_rains'
  | 'win_pre_long_rains'
  | 'win_long_rains'
  | 'win_dry';

const EN: Record<Key, string> = {
  next: 'Next',
  yes: 'Yes',
  no: 'No',
  take_photo: 'Take photo',
  upload: 'Choose photo',
  sample: 'Try a sample plot',
  retake: 'Take again',
  skip: 'Skip this photo',
  done: 'See result',
  of: 'of',
  leaves: 'leaves',
  rust: 'Rust',
  no_problem: 'No problem seen',
  other_spots: 'Other spots: ask the officer',
  not_sure: 'Not sure',
  act: 'I will act',
  wait: 'I will wait',
  ask: 'Ask the officer',
  send_sms: 'Send SMS',
  history: 'History',
  new_check: 'New check',
  start_again: 'Start again',
  mock: 'MOCK MODEL: results are not real',
  offline_ready: 'Works offline',
  offline_not_ready: 'Saving for offline use',
  not_translated: 'Not translated yet',
  machine_draft: 'Machine translation, pending review',
  draft: 'Draft, pending review',
  model_missing: 'Model not loaded: every leaf shows as not sure',
  photos_ok: 'photos OK',
  to_retake: 'Take again',
  checking: 'Checking',
  chars: 'characters',
  demo_number: 'Demo number, not a real cooperative line',
  assumption: 'Assumption',
  sources: 'Sources',
  no_checks: 'No checks yet',
  credits: 'Photo credits',
  sample_note: 'Sample photos from public sources, not from Kenya. Labels not checked by an agronomist.',
  back: 'Back',
  my_farm: 'My farm',
  which_block: 'Which coffee block are the leaves from?',
  tap_block: 'Tap a coffee block',
  coffee: 'Coffee',
  maize: 'Maize',
  beans: 'Beans',
  home: 'House',
  upper_slope: 'Upper slope',
  coffee_only: 'Leaf check: coffee only',
  check_block: 'Check',
  check_next: 'Check next',
  status_ok: 'No problem seen',
  status_watch: 'Watch',
  status_act: 'Act',
  status_ask: 'Ask the officer',
  status_none: 'Not checked yet',
  overdue: 'time to check again',
  last_check: 'Last check',
  days_ago: 'days ago',
  day_ago: '1 day ago',
  today: 'today',
  check_again_by: 'Check again by',
  example: 'Show an example farm',
  hide_example: 'Hide example',
  example_note: 'Example data, synthetic. Not saved.',
  schematic_note: 'Schematic of a 2 ha farm, not to scale. Block layout is illustrative. Coffee blocks are coloured by the last leaf check saved on this phone.',
  unassigned: 'earlier checks have no block',
  now_window: 'Now',
  win_pre_short_rains: 'Before the short rains',
  win_short_rains: 'Short rains',
  win_pre_long_rains: 'Before the long rains',
  win_long_rains: 'Long rains',
  win_dry: 'Dry season',
};

// Builder draft, pending native review.
const SW: Partial<Record<Key, string>> = {
  next: 'Endelea',
  yes: 'Ndiyo',
  no: 'Hapana',
  take_photo: 'Piga picha',
  upload: 'Chagua picha',
  sample: 'Jaribu shamba la mfano',
  retake: 'Piga tena',
  skip: 'Ruka picha hii',
  done: 'Ona jibu',
  of: 'kati ya',
  leaves: 'majani',
  rust: 'Kutu',
  no_problem: 'Hakuna tatizo',
  other_spots: 'Madoa mengine: muulize afisa',
  not_sure: 'Hatuna uhakika',
  act: 'Nitachukua hatua',
  wait: 'Nitasubiri',
  ask: 'Muulize afisa',
  send_sms: 'Tuma SMS',
  history: 'Historia',
  new_check: 'Ukaguzi mpya',
  start_again: 'Anza tena',
  my_farm: 'Shamba langu',
  which_block: 'Majani yametoka kitalu kipi cha kahawa?',
  tap_block: 'Gusa kitalu cha kahawa',
  coffee: 'Kahawa',
  maize: 'Mahindi',
  beans: 'Maharagwe',
  home: 'Nyumbani',
  upper_slope: 'Juu ya mteremko',
  coffee_only: 'Ukaguzi wa majani: kahawa tu',
  check_block: 'Kagua',
  check_next: 'Kagua kwanza',
  status_ok: 'Hakuna tatizo',
  status_watch: 'Fuatilia',
  status_act: 'Chukua hatua',
  status_ask: 'Muulize afisa',
  status_none: 'Bado haijakaguliwa',
  overdue: 'wakati wa kukagua tena',
  last_check: 'Ukaguzi wa mwisho',
  days_ago: 'siku zilizopita',
  day_ago: 'jana',
  today: 'leo',
  check_again_by: 'Kagua tena kabla ya',
  example: 'Onyesha shamba la mfano',
  hide_example: 'Ficha mfano',
  now_window: 'Sasa',
  win_pre_short_rains: 'Kabla ya mvua za vuli',
  win_short_rains: 'Mvua za vuli',
  win_pre_long_rains: 'Kabla ya masika',
  win_long_rains: 'Masika',
  win_dry: 'Kiangazi',
};

export function windowLabel(w: SeasonWindow, lang: Lang): string {
  return t(`win_${w}` as Key, lang);
}

export function t(key: Key, lang: Lang): string {
  if (lang === 'en') return EN[key];
  return SW[key] ?? EN[key];
}

export interface CardText {
  text: string;
  notSure: string | null;
  /** Language actually shown. */
  shown: Lang;
  /** Tag to show under the text when it is not in the chosen language, or is a machine or unreviewed draft. */
  tag: string | null;
}

/** Text of an answer card in the chosen language, falling back to Swahili, then English. */
export function cardText(card: AnswerCard, lang: Lang): CardText {
  const order: Lang[] = lang === 'en' ? ['en', 'sw'] : lang === 'sw' ? ['sw', 'en'] : ['kik', 'sw', 'en'];
  const shown = order.find((l) => card.text[l]) ?? 'en';
  const text = card.text[shown] ?? '';
  const notSure = card.notSure?.[shown] ?? card.notSure?.en ?? null;
  let tag: string | null = null;
  if (shown !== lang) tag = t('not_translated', 'en');
  else if (/machine/.test(card.reviewStatus?.[shown] ?? '')) tag = t('machine_draft', 'en');
  else if (/draft/.test(card.reviewStatus?.[shown] ?? '')) tag = t('draft', 'en');
  return { text, notSure, shown, tag };
}

/** The card if answers.json has it, else null (getAnswer falls back to ask_officer). */
export function cardIfExists(id: string): AnswerCard | null {
  const c = getAnswer(id);
  return c.id === id ? c : null;
}

/** Name of each language in its own words, from answers.json language_name. */
export function languageName(lang: Lang): string {
  const c = cardIfExists('language_name');
  return c?.text[lang] ?? { sw: 'Kiswahili', kik: 'Gikuyu', en: 'English' }[lang];
}
