import { checkQuality } from './quality.ts'
import { classifyRgba, consumeMockHint } from './model.mock.ts'
import type { LeafResult } from './types.ts'

export interface ModelInfo {
  version: string
  mock: boolean
}

/**
 * The trained int8 ONNX file is not in this copy. Every label comes from the
 * mock (file name, sample name, or a colour guess). The screen keeps the
 * mock badge on. Do not report a real model version until onnxruntime-web
 * runs the exported network.
 */
export async function loadModel(): Promise<ModelInfo> {
  return { version: 'mock', mock: true }
}

export function modelInfo(): ModelInfo {
  return { version: 'mock', mock: true }
}

export async function classifyLeaf(img: ImageBitmap): Promise<LeafResult> {
  const hint = consumeMockHint()
  const quality = checkQuality(img)
  const canvas = document.createElement('canvas')
  canvas.width = img.width
  canvas.height = img.height
  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) return classifyRgba(img.width, img.height, new Uint8ClampedArray(img.width * img.height * 4), hint, quality)
  ctx.drawImage(img, 0, 0)
  const data = ctx.getImageData(0, 0, img.width, img.height)
  return classifyRgba(data.width, data.height, data.data, hint, quality)
}
