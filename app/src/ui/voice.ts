// Speaker button logic. Recorded clips (public/audio/<lang>/<id>.mp3) play through the engine.
// When no clip exists for the language or its Swahili fallback, the phone's own offline voice
// reads the text (only voices that run on the device: localService). If neither exists the
// button does nothing; the screen never shows an audio error.
import { play, stop, type Lang } from '../engine';

const CLIPS = new Set<string>(typeof __JANI_AUDIO__ !== 'undefined' ? __JANI_AUDIO__ : []);

export function hasClip(id: string, lang: Lang): boolean {
  return CLIPS.has(`${lang}/${id}`);
}

const BCP47: Record<Lang, string> = { sw: 'sw', kik: 'ki', en: 'en' };

function deviceVoice(lang: Lang): SpeechSynthesisVoice | null {
  if (typeof speechSynthesis === 'undefined') return null;
  const voices = speechSynthesis.getVoices().filter((v) => v.localService);
  return voices.find((v) => v.lang.toLowerCase().startsWith(BCP47[lang])) ?? null;
}

export function stopVoice(): void {
  stop();
  try {
    if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
  } catch {
    // ignore
  }
}

/** Plays the clip for an answer id, or reads `text` with an on-device voice. Never throws. */
export async function speak(id: string | null, lang: Lang, text: string, textLang: Lang = lang): Promise<void> {
  stopVoice();
  try {
    if (id && (hasClip(id, lang) || hasClip(id, 'sw'))) {
      await play(id, lang);
      return;
    }
    const voice = deviceVoice(textLang);
    if (!voice || !text) return;
    const u = new SpeechSynthesisUtterance(text);
    u.voice = voice;
    u.lang = voice.lang;
    u.rate = 0.9;
    speechSynthesis.speak(u);
  } catch {
    // text stays on screen
  }
}
