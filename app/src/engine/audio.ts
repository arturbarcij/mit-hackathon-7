// Voice playback for answer cards. Plays /audio/<lang>/<id>.mp3, falls back to Swahili,
// then to text only (resolves quietly). play() never throws or rejects.
// SSR-safe: Audio is only touched inside play().
import type { Lang } from './types';

/** The subset of HTMLAudioElement we use, so tests can pass a fake. */
export interface AudioLike {
  play(): Promise<void> | void;
  pause(): void;
  onended: ((ev: Event) => unknown) | null;
  onerror: OnErrorEventHandler | ((ev: Event) => unknown) | null;
}

type AudioFactory = (src: string) => AudioLike;

let factory: AudioFactory | null = null;
let current: { el: AudioLike; cancel: () => void } | null = null;
let seq = 0;

/** Test hook: replace the Audio constructor. Pass null to restore the default. */
export function _setAudioFactory(fn: AudioFactory | null): void {
  factory = fn;
}

export function audioPath(answerId: string, lang: Lang): string {
  return `/audio/${lang}/${answerId}.mp3`;
}

/** Stops whatever is playing. Safe to call at any time. */
export function stop(): void {
  const c = current;
  current = null;
  if (!c) return;
  try {
    c.el.pause();
  } catch {
    // ignore
  }
  c.cancel();
}

type Outcome = 'ended' | 'failed' | 'stopped';

function tryPlay(src: string): Promise<Outcome> {
  return new Promise<Outcome>((resolve) => {
    let el: AudioLike;
    try {
      el = factory ? factory(src) : (new Audio(src) as unknown as AudioLike);
    } catch {
      resolve('failed');
      return;
    }
    let done = false;
    const finish = (o: Outcome) => {
      if (done) return;
      done = true;
      if (current?.el === el) current = null;
      el.onended = null;
      el.onerror = null;
      resolve(o);
    };
    el.onended = () => finish('ended');
    el.onerror = () => finish('failed');
    current = { el, cancel: () => finish('stopped') };
    try {
      const p = el.play();
      if (p && typeof p.then === 'function') p.then(undefined, () => finish('failed'));
    } catch {
      finish('failed');
    }
  });
}

/** Plays the clip for an answer. Resolves when it ends, is stopped, or nothing could play. */
export async function play(answerId: string, lang: Lang): Promise<void> {
  stop();
  if (!factory && typeof Audio === 'undefined') return;
  const mine = ++seq;
  try {
    const first = await tryPlay(audioPath(answerId, lang));
    if (first === 'failed' && lang !== 'sw' && mine === seq) await tryPlay(audioPath(answerId, 'sw'));
  } catch {
    // text-only fallback
  }
}
