type AnyCanvas = OffscreenCanvas | HTMLCanvasElement;
type AnyContext = OffscreenCanvasRenderingContext2D | CanvasRenderingContext2D;

export function makeCanvas(width: number, height: number): AnyCanvas {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(width, height);
  const c = document.createElement('canvas');
  c.width = width;
  c.height = height;
  return c;
}

function context2d(canvas: AnyCanvas): AnyContext {
  const ctx = canvas.getContext('2d', { willReadFrequently: true }) as AnyContext | null;
  if (!ctx) throw new Error('Canvas 2D is not available on this device');
  return ctx;
}

/** Draws a region of the source into a new canvas of the given size and returns its pixels (RGBA). */
export function drawRegion(
  img: CanvasImageSource,
  sx: number, sy: number, sw: number, sh: number,
  dw: number, dh: number,
): ImageData {
  const canvas = makeCanvas(dw, dh);
  const ctx = context2d(canvas);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, dw, dh);
  return ctx.getImageData(0, 0, dw, dh);
}

export async function canvasToJpeg(canvas: AnyCanvas, quality: number): Promise<Blob> {
  if ('convertToBlob' in canvas) return canvas.convertToBlob({ type: 'image/jpeg', quality });
  return new Promise((resolve, reject) => {
    (canvas as HTMLCanvasElement).toBlob(
      (b) => (b ? resolve(b) : reject(new Error('JPEG encode failed'))),
      'image/jpeg',
      quality,
    );
  });
}

export function drawScaled(img: CanvasImageSource, w: number, h: number): AnyCanvas {
  const canvas = makeCanvas(w, h);
  const ctx = context2d(canvas);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, 0, 0, w, h);
  return canvas;
}
