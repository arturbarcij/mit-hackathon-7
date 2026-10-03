import type { QualityResult } from './types.ts'

/**
 * Quality gate thresholds, set 3 Oct 2026 on synthetic images in tests/engine
 * (flat gradient, near-black, 32 px square, veined leaf). Real phone photos
 * were not available. Retune on 10 sharp and 10 blurred phone photos before
 * calling these numbers final.
 *
 * too_small: shorter side under 64 px.
 * dark: mean luma under 40 (0 to 255).
 * blurry: variance of the Laplacian on a greyscale copy under 25.
 */
export const BLUR_MIN = 25
export const DARK_MAX = 40
export const MIN_SIDE = 64

export function assessRgba(width: number, height: number, rgba: Uint8ClampedArray): QualityResult {
  if (width < MIN_SIDE || height < MIN_SIDE) {
    const brightness = width > 0 && height > 0 ? meanLuma(width, height, rgba) : 0
    return { ok: false, reason: 'too_small', blur: 0, brightness }
  }

  const { gray, w, h } = sampleGray(width, height, rgba, 256)
  const brightness = meanOf(gray)
  if (brightness < DARK_MAX) {
    return { ok: false, reason: 'dark', blur: laplacianVariance(gray, w, h), brightness }
  }

  const blur = laplacianVariance(gray, w, h)
  if (blur < BLUR_MIN) {
    return { ok: false, reason: 'blurry', blur, brightness }
  }

  return { ok: true, blur, brightness }
}

export function checkQuality(img: ImageBitmap): QualityResult {
  const canvas = document.createElement('canvas')
  canvas.width = img.width
  canvas.height = img.height
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) {
    return { ok: false, reason: 'blurry', blur: 0, brightness: 0 }
  }
  ctx.drawImage(img, 0, 0)
  const data = ctx.getImageData(0, 0, img.width, img.height)
  return assessRgba(data.width, data.height, data.data)
}

function meanLuma(width: number, height: number, rgba: Uint8ClampedArray): number {
  const { gray } = sampleGray(width, height, rgba, 64)
  return meanOf(gray)
}

function sampleGray(
  width: number,
  height: number,
  rgba: Uint8ClampedArray,
  maxSide: number,
): { gray: Float32Array; w: number; h: number } {
  const scale = Math.min(1, maxSide / Math.max(width, height))
  const w = Math.max(1, Math.round(width * scale))
  const h = Math.max(1, Math.round(height * scale))
  const gray = new Float32Array(w * h)
  for (let y = 0; y < h; y++) {
    const sy = Math.min(height - 1, Math.floor((y * height) / h))
    for (let x = 0; x < w; x++) {
      const sx = Math.min(width - 1, Math.floor((x * width) / w))
      const i = (sy * width + sx) * 4
      const r = rgba[i] ?? 0
      const g = rgba[i + 1] ?? 0
      const b = rgba[i + 2] ?? 0
      gray[y * w + x] = 0.299 * r + 0.587 * g + 0.114 * b
    }
  }
  return { gray, w, h }
}

function meanOf(values: Float32Array): number {
  let sum = 0
  for (let i = 0; i < values.length; i++) sum += values[i] ?? 0
  return values.length ? sum / values.length : 0
}

function laplacianVariance(gray: Float32Array, w: number, h: number): number {
  if (w < 3 || h < 3) return 0
  let sum = 0
  let sum2 = 0
  let n = 0
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x
      const centre = gray[i] ?? 0
      const lap = centre * 4 - (gray[i - 1] ?? 0) - (gray[i + 1] ?? 0) - (gray[i - w] ?? 0) - (gray[i + w] ?? 0)
      sum += lap
      sum2 += lap * lap
      n++
    }
  }
  if (!n) return 0
  const mean = sum / n
  return sum2 / n - mean * mean
}
