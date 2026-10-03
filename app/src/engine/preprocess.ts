export interface RgbaImage {
  data: Uint8ClampedArray | Uint8Array;
  width: number;
  height: number;
}

export interface NormaliseSpec {
  size: number;
  mean: number[];
  std: number[];
}

function sample(data: Uint8ClampedArray | Uint8Array, width: number, height: number, x: number, y: number, channel: number): number {
  const xx = Math.min(width - 1, Math.max(0, x));
  const yy = Math.min(height - 1, Math.max(0, y));
  return data[(yy * width + xx) * 4 + channel];
}

export function resizeShorterSide(image: RgbaImage, shorter: number): RgbaImage {
  const { width, height, data } = image;
  const minSide = Math.min(width, height);
  if (minSide === shorter) return image;
  const scale = shorter / minSide;
  let dstW = Math.round(width * scale);
  let dstH = Math.round(height * scale);
  if (width <= height) {
    dstW = shorter;
    dstH = Math.max(shorter, Math.round(height * (shorter / width)));
  } else {
    dstH = shorter;
    dstW = Math.max(shorter, Math.round(width * (shorter / height)));
  }
  const out = new Uint8ClampedArray(dstW * dstH * 4);
  for (let y = 0; y < dstH; y++) {
    const srcY = (y + 0.5) * (height / dstH) - 0.5;
    const y0 = Math.floor(srcY);
    const wy = srcY - y0;
    for (let x = 0; x < dstW; x++) {
      const srcX = (x + 0.5) * (width / dstW) - 0.5;
      const x0 = Math.floor(srcX);
      const wx = srcX - x0;
      const index = (y * dstW + x) * 4;
      for (let channel = 0; channel < 4; channel++) {
        const p00 = sample(data, width, height, x0, y0, channel);
        const p10 = sample(data, width, height, x0 + 1, y0, channel);
        const p01 = sample(data, width, height, x0, y0 + 1, channel);
        const p11 = sample(data, width, height, x0 + 1, y0 + 1, channel);
        const value =
          p00 * (1 - wx) * (1 - wy) +
          p10 * wx * (1 - wy) +
          p01 * (1 - wx) * wy +
          p11 * wx * wy;
        out[index + channel] = Math.round(value);
      }
    }
  }
  return { data: out, width: dstW, height: dstH };
}

export function centreCrop(image: RgbaImage, size: number): RgbaImage {
  const left = Math.floor((image.width - size) / 2);
  const top = Math.floor((image.height - size) / 2);
  const out = new Uint8ClampedArray(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const index = (y * size + x) * 4;
      for (let channel = 0; channel < 4; channel++) {
        out[index + channel] = sample(image.data, image.width, image.height, left + x, top + y, channel);
      }
    }
  }
  return { data: out, width: size, height: size };
}

export function toNchw(image: RgbaImage, mean: number[], std: number[]): Float32Array {
  const plane = image.width * image.height;
  const out = new Float32Array(3 * plane);
  for (let i = 0; i < plane; i++) {
    const red = image.data[i * 4] / 255;
    const green = image.data[i * 4 + 1] / 255;
    const blue = image.data[i * 4 + 2] / 255;
    out[i] = (red - mean[0]) / std[0];
    out[plane + i] = (green - mean[1]) / std[1];
    out[2 * plane + i] = (blue - mean[2]) / std[2];
  }
  return out;
}

export function imageToNchw(image: RgbaImage, spec: NormaliseSpec): Float32Array {
  const resized = resizeShorterSide(image, spec.size);
  const cropped = centreCrop(resized, spec.size);
  return toNchw(cropped, spec.mean, spec.std);
}

export function readImageBitmap(img: ImageBitmap): RgbaImage {
  const { width, height } = img;
  if (typeof OffscreenCanvas !== 'undefined') {
    const canvas = new OffscreenCanvas(width, height);
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Could not read the leaf photo');
    context.drawImage(img, 0, 0);
    const pixels = context.getImageData(0, 0, width, height);
    return { data: pixels.data, width, height };
  }
  if (typeof document === 'undefined') throw new Error('Could not read the leaf photo');
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Could not read the leaf photo');
  context.drawImage(img, 0, 0);
  const pixels = context.getImageData(0, 0, width, height);
  return { data: pixels.data, width, height };
}
