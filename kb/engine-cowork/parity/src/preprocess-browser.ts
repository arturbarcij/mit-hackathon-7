/**
 * preprocess-browser.ts
 *
 * Browser glue for preprocess.ts. Gets RGBA pixels out of a File, Blob,
 * ImageBitmap or HTMLImageElement at NATIVE size. No scaling happens in the
 * canvas, so canvas resampling never enters the pipeline. All resizing is done
 * by preprocess.ts, which reproduces Pillow.
 *
 * Caveats the engine agent must know:
 * 1. JPEG decoding. The browser decodes JPEG with its own decoder (Chromium:
 *    libjpeg-turbo). PIL also uses libjpeg(-turbo). Both do "fancy" chroma
 *    upsampling, but IDCT and colour conversion can differ by 1 or 2 levels on
 *    some pixels. Measured numbers are in RESULTS.json / README.md.
 * 2. EXIF orientation. createImageBitmap applies EXIF rotation by default
 *    (imageOrientation: 'from-image'). PIL in train.py does NOT apply it.
 *    Training data was mostly dataset images without EXIF, so this helper
 *    keeps the browser default (upright image) because that is what the
 *    farmer sees. Set `imageOrientation: 'none'` if strict parity with
 *    PIL on EXIF-rotated phone photos is ever required.
 * 3. Colour management. Canvas pixels are sRGB. An embedded ICC profile is
 *    applied by the browser; PIL ignores it. Phone JPEGs are sRGB, so this
 *    is a no-op in practice. We pass colorSpaceConversion: 'none' where supported.
 * 4. Alpha. We request premultiplyAlpha: 'none'. PIL's convert("RGB") drops
 *    alpha without compositing. Photos have no alpha, so this only matters for
 *    odd PNG inputs.
 */

import { preprocess, type PreprocessResult, type PreprocessSpec, type RawImage, DEFAULT_SPEC } from './preprocess';

export type ImageSource = Blob | ImageBitmap | HTMLImageElement | HTMLCanvasElement | OffscreenCanvas;

function makeCanvas(w: number, h: number): OffscreenCanvas | HTMLCanvasElement {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(w, h);
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return c;
}

/** Draw the source at native size and read back RGBA. */
export async function toRawImage(src: ImageSource): Promise<RawImage> {
  let bmp: ImageBitmap | HTMLImageElement | HTMLCanvasElement | OffscreenCanvas;
  let owned = false;
  if (src instanceof Blob) {
    bmp = await createImageBitmap(src, {
      premultiplyAlpha: 'none',
      colorSpaceConversion: 'none',
    } as ImageBitmapOptions);
    owned = true;
  } else {
    bmp = src;
  }
  const w = (bmp as ImageBitmap).width ?? (bmp as HTMLImageElement).naturalWidth;
  const h = (bmp as ImageBitmap).height ?? (bmp as HTMLImageElement).naturalHeight;
  const canvas = makeCanvas(w, h);
  const ctx = canvas.getContext('2d', { willReadFrequently: true, alpha: false } as never) as
    | OffscreenCanvasRenderingContext2D
    | CanvasRenderingContext2D;
  if (!ctx) throw new Error('2d canvas context unavailable');
  ctx.drawImage(bmp as CanvasImageSource, 0, 0); // 1:1, no scaling
  const id = ctx.getImageData(0, 0, w, h);
  if (owned) (bmp as ImageBitmap).close();
  return { data: id.data, width: w, height: h };
}

/** File/Blob/ImageBitmap in, NCHW float32 tensor out. */
export async function preprocessImage(src: ImageSource, spec: PreprocessSpec = DEFAULT_SPEC): Promise<PreprocessResult> {
  const raw = await toRawImage(src);
  return preprocess(raw, spec);
}
