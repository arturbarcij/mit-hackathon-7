export type SampleKind = 'rust' | 'healthy' | 'blur' | 'dark' | 'not_leaf' | 'phoma' | 'miner' | 'cercospora'

const SIZE = 160

/** Synthetic stand-in pictures for tests and for a demo without farm leaves. */
export function makeSample(kind: SampleKind): { width: number; height: number; rgba: Uint8ClampedArray } {
  const width = kind === 'blur' ? 96 : SIZE
  const height = kind === 'blur' ? 96 : SIZE
  const rgba = new Uint8ClampedArray(width * height * 4)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const [r, g, b] = pixel(kind, x, y, width, height)
      const i = (y * width + x) * 4
      rgba[i] = r
      rgba[i + 1] = g
      rgba[i + 2] = b
      rgba[i + 3] = 255
    }
  }
  return { width, height, rgba }
}

function pixel(kind: SampleKind, x: number, y: number, w: number, h: number): [number, number, number] {
  if (kind === 'dark') return [12, 14, 12]
  if (kind === 'blur') {
    const t = x / w
    const v = 70 + Math.round(t * 40)
    return [v - 20, v + 30, v - 25]
  }
  if (kind === 'not_leaf') {
    const bar = Math.floor(x / 12) % 2 === 0
    return bar ? [30, 70, 190] : [230, 230, 235]
  }

  const leaf: [number, number, number] = [36, 122, 48]
  const vein = x % 14 < 2 || y % 18 < 2
  let r = vein ? 18 : leaf[0]
  let g = vein ? 70 : leaf[1]
  let b = vein ? 28 : leaf[2]

  if (kind === 'rust' && inSpot(x, y, 16, 5)) {
    r = 214
    g = 118
    b = 28
  }
  if (kind === 'cercospora' && inRing(x, y, 22)) {
    r = 150
    g = 96
    b = 42
  }
  if (kind === 'phoma' && inSpot(x, y, 20, 7)) {
    r = 48
    g = 36
    b = 32
  }
  if (kind === 'miner' && inBlotch(x, y)) {
    r = 132
    g = 86
    b = 48
  }
  if (kind === 'healthy') {
    void h
  }
  return [r, g, b]
}

function inSpot(x: number, y: number, step: number, radius: number): boolean {
  const cx = Math.floor(x / step) * step + step / 2
  const cy = Math.floor(y / step) * step + step / 2
  const dx = x - cx
  const dy = y - cy
  return dx * dx + dy * dy < radius * radius
}

function inRing(x: number, y: number, step: number): boolean {
  const cx = Math.floor(x / step) * step + step / 2
  const cy = Math.floor(y / step) * step + step / 2
  const d = Math.hypot(x - cx, y - cy)
  return d > 4 && d < 8
}

function inBlotch(x: number, y: number): boolean {
  const wave = Math.sin(x / 6) * 8
  return y > 40 && y < 70 + wave && x % 40 < 24
}
