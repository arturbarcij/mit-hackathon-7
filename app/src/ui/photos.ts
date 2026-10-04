// Photo input for the capture screen: camera or file to ImageBitmap, and the bundled sample plot.
import { classifyLeaf, getAnswer, type ImageInput, type LeafResult } from '../engine';
import { drawToRgba } from '../engine/image';

export interface Photo {
  /** Object URL for the thumbnail. */
  url: string;
  bitmap: ImageBitmap;
  /** Bundled demo photo (the sheet gate is skipped for these). */
  sample: boolean;
  name: string;
}

/** Decodes a file to an ImageBitmap, honouring EXIF rotation. Null when it cannot be decoded. */
export async function decodeFile(file: Blob, name: string, sample = false): Promise<Photo | null> {
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
    return { url: URL.createObjectURL(file), bitmap, sample, name };
  } catch {
    return null;
  }
}

export interface SampleItem {
  file: string;
  local_path: string;
  role: string;
  attribution: string;
}

export interface SampleManifest {
  note: string;
  items: SampleItem[];
}

/** The sample plot: 10 leaves (6 rust, 3 healthy, 1 other problem by source hint). */
export const SAMPLE_PLOT_SIZE = 10;

export async function loadSampleManifest(): Promise<SampleManifest> {
  const res = await fetch(`${import.meta.env.BASE_URL}demo/manifest.json`);
  if (!res.ok) throw new Error(`demo manifest HTTP ${res.status}`);
  return (await res.json()) as SampleManifest;
}

export async function loadSamplePhotos(m: SampleManifest): Promise<Photo[]> {
  const out: Photo[] = [];
  for (const item of m.items.slice(0, SAMPLE_PLOT_SIZE)) {
    const res = await fetch(`${import.meta.env.BASE_URL}demo/${item.file}`);
    if (!res.ok) continue;
    const p = await decodeFile(await res.blob(), item.file, true);
    if (p) out.push(p);
  }
  return out;
}

export type RetakeId = 'retake_blurry' | 'retake_dark' | 'retake_on_page' | 'not_a_leaf';

/** Which retake card a result needs, if any. Uses retake_on_page only when answers.json has it. */
export function retakeId(r: LeafResult): RetakeId | null {
  const reason = r.quality && !r.quality.ok ? (r.quality.reason as string | undefined) : undefined;
  if (r.quality && !r.quality.ok) {
    if (reason === 'dark') return 'retake_dark';
    if (reason === 'not_on_page') return getAnswer('retake_on_page').id === 'retake_on_page' ? 'retake_on_page' : 'retake_blurry';
    return 'retake_blurry';
  }
  if (r.label === 'not_leaf') return 'not_a_leaf';
  return null;
}

type ClassifyWithOptions = (img: ImageInput, opts?: { sheetGate?: boolean }) => Promise<LeafResult>;

/** Classifies one photo. Bundled samples skip the sheet gate (engine option; ignored by older engines). */
export async function classifyPhoto(p: Photo): Promise<LeafResult> {
  return (classifyLeaf as ClassifyWithOptions)(p.bitmap, p.sample ? { sheetGate: false } : undefined);
}

/**
 * Key of an 8x8 grey thumbnail (6 bits per cell), used to drop the same photo added twice.
 * Null when there is no canvas: then nothing is dropped (never a size-only key, which would
 * treat different photos of the same size as one).
 */
export function photoHash(bitmap: ImageBitmap | null | undefined): string | null {
  if (!bitmap) return null;
  try {
    const { data } = drawToRgba(bitmap, 8, 8);
    let key = '';
    for (let i = 0; i < 64; i++) key += String.fromCharCode(48 + (((data[i * 4] + data[i * 4 + 1] + data[i * 4 + 2]) / 3) >> 2));
    return key;
  } catch {
    return null;
  }
}
