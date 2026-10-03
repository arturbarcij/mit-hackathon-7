import type { Lang } from './types';

let current: HTMLAudioElement | null = null;

const base = () => import.meta.env.BASE_URL ?? '/';

export function audioUrl(answerId: string, lang: Lang): string {
  return `${base()}audio/${lang}/${encodeURIComponent(answerId)}.mp3`;
}

/** Order of attempts: the chosen language, then Swahili, then nothing (text only). */
export function audioFallbackChain(lang: Lang): Lang[] {
  return lang === 'sw' ? ['sw'] : [lang, 'sw'];
}

type Outcome = 'played' | 'missing' | 'blocked';

function tryPlay(url: string): Promise<Outcome> {
  return new Promise((resolve) => {
    if (typeof Audio === 'undefined') {
      resolve('missing');
      return;
    }
    const el = new Audio(url);
    current = el;
    el.addEventListener('ended', () => resolve('played'), { once: true });
    el.addEventListener('pause', () => resolve('played'), { once: true });
    el.addEventListener('error', () => resolve('missing'), { once: true });
    el.play().catch((e: unknown) => {
      // NotAllowedError means the browser wants a tap first; another language file would hit the same wall.
      resolve((e as { name?: string })?.name === 'NotAllowedError' ? 'blocked' : 'missing');
    });
  });
}

/**
 * Plays public/audio/<lang>/<answerId>.mp3 and resolves when it ends. Never rejects: if the clip is
 * missing it tries Swahili, and if that is missing too it resolves quietly so the UI shows text only.
 */
export async function play(answerId: string, lang: Lang): Promise<void> {
  stop();
  for (const l of audioFallbackChain(lang)) {
    const outcome = await tryPlay(audioUrl(answerId, l));
    if (outcome !== 'missing') return;
  }
}

export function stop(): void {
  if (current) {
    current.pause();
    current = null;
  }
}
