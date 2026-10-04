// Engine entry point used by the UI. Owned by the engine lane (kb/OWNERSHIP.md).
// Real now: summarisePlot, seasonWindow, seasonClock, decide (rules.json), answer cards (answers.json),
// quality gate (blur and brightness), JANI1 referral SMS, audio playback of pre-rendered clips.
// Mock until the ml lane ships public/model/leaf.onnx: classifyLeaf uses a colour rule and loadModel reports mock.
import { analyse, mockClassify, MOCK_VERSION } from "./vision";
import type { Lang, LeafResult, QualityResult } from "./types";

export type {
  AnswerCard,
  Decision,
  Label,
  Lang,
  LeafResult,
  PlotSummary,
  QualityResult,
  ReferralCheck,
  ReferralInput,
  SeasonClock,
  SeasonWindow,
} from "./types";
export {
  answerCard,
  buildReferral,
  cardText,
  decide,
  decideId,
  DISEASES,
  explain,
  LABELS,
  meanConfidence,
  normalisePlot,
  seasonClock,
  seasonWindow,
  SMS_MAX,
  summarisePlot,
} from "./decision";
export { ABSTAIN_BELOW, QUALITY } from "./vision";

export async function loadModel(): Promise<{ version: string; mock: boolean }> {
  return { version: MOCK_VERSION, mock: true };
}

type Drawable = ImageBitmap | HTMLImageElement | HTMLCanvasElement;

export function checkQuality(img: Drawable): QualityResult {
  return analyse(img).quality;
}

export async function classifyLeaf(img: Drawable): Promise<LeafResult> {
  const { stats, quality } = analyse(img);
  return mockClassify(stats, quality);
}

export function smsLink(number: string, body: string): string {
  const ua = typeof navigator === "undefined" ? "" : navigator.userAgent;
  const separator = /iPhone|iPad|iPod/i.test(ua) ? "&" : "?";
  return `sms:${number.replace(/[^\d+]/g, "")}${separator}body=${encodeURIComponent(body)}`;
}

let current: HTMLAudioElement | null = null;

/** Plays /audio/<lang>/<answerId>.mp3 if it exists. Resolves false when there is no clip (nothing is generated at runtime). */
export function play(answerId: string, lang: Lang): Promise<boolean> {
  if (typeof Audio === "undefined") return Promise.resolve(false);
  current?.pause();
  const audio = new Audio(`/audio/${lang}/${answerId}.mp3`);
  current = audio;
  return new Promise((resolve) => {
    audio.onended = () => resolve(true);
    audio.onerror = () => resolve(false);
    audio.play().catch(() => resolve(false));
  });
}

export function stopAudio(): void {
  current?.pause();
  current = null;
}
