import type { Lang } from './types.ts';

export function resolveAudioUrl(answerId: string, lang: Lang, existing: Set<string>): string | null {
  const preferred = `/audio/${lang}/${answerId}.mp3`;
  if (existing.has(preferred)) return preferred;
  const swahili = `/audio/sw/${answerId}.mp3`;
  if (existing.has(swahili)) return swahili;
  return null;
}

function tryPlay(url: string): Promise<boolean> {
  if (typeof Audio === 'undefined') return Promise.resolve(false);
  return new Promise((resolve) => {
    try {
      const audio = new Audio(url);
      let settled = false;
      const finish = (ok: boolean) => {
        if (settled) return;
        settled = true;
        resolve(ok);
      };
      audio.addEventListener('error', () => finish(false));
      void audio.play().then(() => finish(true)).catch(() => finish(false));
    } catch {
      resolve(false);
    }
  });
}

export async function play(answerId: string, lang: Lang): Promise<void> {
  const urls = lang === 'sw'
    ? [`/audio/sw/${answerId}.mp3`]
    : [`/audio/${lang}/${answerId}.mp3`, `/audio/sw/${answerId}.mp3`];
  for (const url of urls) {
    const played = await tryPlay(url);
    if (played) return;
  }
}
