// Canvas helpers shared by the quality gate, the model and the mock model.
// SSR-safe: nothing here touches the DOM until a function is called.
import type { ImageInput } from './types';

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Rgba {
  data: Uint8ClampedArray;
  width: number;
  height: number;
}

/** Thrown when neither OffscreenCanvas nor a document canvas is available (SSR, node). */
export class NoCanvasError extends Error {
  constructor(detail = 'no OffscreenCanvas and no document canvas in this environment') {
    super(`Canvas unavailable: ${detail}`);
    this.name = 'NoCanvasError';
  }
}

type Canvas2D = OffscreenCanvasRenderingContext2D | CanvasRenderingContext2D;

export function makeCanvas(w: number, h: number): OffscreenCanvas | HTMLCanvasElement {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
  if (typeof document !== 'undefined' && typeof document.createElement === 'function') {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
  }
  throw new NoCanvasError();
}

/** Square crop of the shorter side, centred. Pure. */
export function centerCropRect(w: number, h: number): Rect {
  const side = Math.min(w, h);
  return { x: Math.floor((w - side) / 2), y: Math.floor((h - side) / 2), w: side, h: side };
}

export function imageSize(img: ImageInput): { width: number; height: number } {
  const el = img as { naturalWidth?: number; naturalHeight?: number; width: number; height: number };
  const width = el.naturalWidth || el.width || 0;
  const height = el.naturalHeight || el.height || 0;
  return { width, height };
}

/** Draws img (optionally a source crop of it) scaled to outW x outH and returns the RGBA pixels. */
export function drawToRgba(img: ImageInput, outW: number, outH: number, crop?: Rect): Rgba {
  const canvas = makeCanvas(outW, outH);
  const ctx = canvas.getContext('2d', { willReadFrequently: true }) as Canvas2D | null;
  if (!ctx) throw new NoCanvasError('canvas has no 2d context');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  const src = crop ?? { x: 0, y: 0, ...wh(imageSize(img)) };
  ctx.drawImage(img as CanvasImageSource, src.x, src.y, src.w, src.h, 0, 0, outW, outH);
  const { data } = ctx.getImageData(0, 0, outW, outH);
  return { data, width: outW, height: outH };
}

function wh(s: { width: number; height: number }): { w: number; h: number } {
  return { w: s.width, h: s.height };
}

/** Hard cap on decoded pixels for the model path (about 24 MP, 96 MB RGBA). Larger photos are scaled down first. */
export const MAX_NATIVE_PIXELS = 24_000_000;

/**
 * RGBA pixels of img at its native size (no canvas scaling, so preprocess.ts can reproduce
 * Pillow's bilinear resize exactly). Uses OffscreenCanvas when available, else a DOM canvas.
 * Only photos above MAX_NATIVE_PIXELS are scaled (by the canvas) to stay within memory.
 */
export function readNativeRgba(img: ImageInput): Rgba {
  const { width, height } = imageSize(img);
  if (!(width > 0 && height > 0)) throw new Error('image has no size');
  const px = width * height;
  if (px <= MAX_NATIVE_PIXELS) return drawToRgba(img, width, height);
  const k = Math.sqrt(MAX_NATIVE_PIXELS / px);
  return drawToRgba(img, Math.max(1, Math.floor(width * k)), Math.max(1, Math.floor(height * k)));
}

/**
 * Decodes a photo file at native size. createImageBitmap when available (applies EXIF
 * orientation, as Chrome does for <img>), else an <img> element via an object URL.
 */
export async function decodeImage(blob: Blob): Promise<ImageBitmap | HTMLImageElement> {
  if (typeof createImageBitmap === 'function') {
    try {
      return await createImageBitmap(blob);
    } catch (err) {
      if (typeof Image === 'undefined') throw err;
    }
  }
  if (typeof Image === 'undefined' || typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
    throw new NoCanvasError('no createImageBitmap and no Image element to decode the photo');
  }
  const url = URL.createObjectURL(blob);
  try {
    const el = new Image();
    el.decoding = 'async';
    await new Promise<void>((ok, fail) => {
      el.onload = () => ok();
      el.onerror = () => fail(new Error('could not decode the photo'));
      el.src = url;
    });
    return el;
  } finally {
    URL.revokeObjectURL(url);
  }
}
