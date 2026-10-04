// Mock leaf model for demos and UI work before the real model exists.
// Deterministic per image: the same photo always gives the same result.
// The UI shows a "mock model" badge whenever loadModel() reports mock: true.
import { drawToRgba, imageSize } from './image';
import { LABELS, type ImageInput, type Label, type LeafResult, type QualityResult } from './types';
import { toLeafResult } from './model';

export const MOCK_VERSION = 'mock';
export const MOCK_THRESHOLD = 0.6;

// Weighted so a demo plot shows mostly healthy and rust, with some of everything else.
const MOCK_MIX: Label[] = ['healthy', 'healthy', 'healthy', 'rust', 'rust', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];

/** FNV-1a over an 8x8 grey thumbnail, or over width and height when there is no canvas. */
export function imageHash(img: ImageInput): number {
  let bytes: number[];
  try {
    const { data } = drawToRgba(img, 8, 8);
    bytes = [];
    for (let i = 0; i < 64; i++) bytes.push((data[i * 4] + data[i * 4 + 1] + data[i * 4 + 2]) / 3 >> 2);
  } catch {
    const { width, height } = imageSize(img);
    bytes = [width & 255, (width >> 8) & 255, height & 255, (height >> 8) & 255];
  }
  let h = 0x811c9dc5;
  for (const b of bytes) {
    h ^= b;
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Small seeded PRNG (mulberry32). */
function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mockClassify(img: ImageInput, quality: QualityResult): LeafResult {
  const seed = imageHash(img);
  const rand = rng(seed);
  const unsure = rand() < 1 / 6; // about 1 in 6 photos abstain
  const top = MOCK_MIX[Math.floor(rand() * MOCK_MIX.length)];
  const others = LABELS.filter((l) => l !== top);
  const second = others[Math.floor(rand() * others.length)];
  // Accepted: top 0.65 to 0.95. Unsure: top 0.34 to 0.5, below MOCK_THRESHOLD.
  const pTop = unsure ? 0.34 + rand() * 0.16 : 0.65 + rand() * 0.3;
  const rest = 1 - pTop;
  const probs = LABELS.map((l) => (l === top ? pTop : l === second ? rest / 2 : rest / 2 / (LABELS.length - 2)));
  return toLeafResult(probs, { labels: [...LABELS], threshold: MOCK_THRESHOLD, version: MOCK_VERSION }, quality);
}
