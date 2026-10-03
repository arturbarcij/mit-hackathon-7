import { drawRegion } from './canvas';
import type { ModelConfig } from './types';

/**
 * Converts RGBA pixels (size x size) to a normalised NCHW float tensor, exactly as model.json says:
 * RGB, scaled to 0 to 1 (unless range is "0-255"), then (x - mean) / std per channel.
 */
export function rgbaToTensor(rgba: Uint8ClampedArray | Uint8Array, size: number, cfg: ModelConfig['input']): Float32Array {
  const plane = size * size;
  const out = new Float32Array(3 * plane);
  const scale = cfg.range === '0-255' ? 1 : 1 / 255;
  for (let i = 0; i < plane; i++) {
    const o = i * 4;
    out[i] = (rgba[o] * scale - cfg.mean[0]) / cfg.std[0];
    out[plane + i] = (rgba[o + 1] * scale - cfg.mean[1]) / cfg.std[1];
    out[2 * plane + i] = (rgba[o + 2] * scale - cfg.mean[2]) / cfg.std[2];
  }
  return out;
}

/**
 * Centre square crop of the source, resized to size x size. Resizing the shorter side to `size`
 * and then centre cropping `size` is the same as cropping the centre square first, so one draw does both.
 * If model.json carries `resize_to` (for example 256 then crop 224), the crop covers size / resize_to of the shorter side.
 */
export function cropRegion(width: number, height: number, size: number, resizeTo?: number) {
  const shorter = Math.min(width, height);
  const side = resizeTo && resizeTo > size ? (shorter * size) / resizeTo : shorter;
  return { sx: (width - side) / 2, sy: (height - side) / 2, side };
}

/** The size x size RGBA crop that feeds the network, before normalisation. */
export function cropForModel(img: ImageBitmap, cfg: ModelConfig['input']): ImageData {
  const { sx, sy, side } = cropRegion(img.width, img.height, cfg.size, cfg.resize_to);
  return drawRegion(img, sx, sy, side, side, cfg.size, cfg.size);
}

export function preprocessBitmap(img: ImageBitmap, cfg: ModelConfig['input']): Float32Array {
  return rgbaToTensor(cropForModel(img, cfg).data, cfg.size, cfg);
}
