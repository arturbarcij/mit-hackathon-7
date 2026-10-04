export async function bitmapFromRgba(width: number, height: number, rgba: Uint8ClampedArray): Promise<ImageBitmap> {
  const copy = new Uint8ClampedArray(rgba)
  return createImageBitmap(new ImageData(copy, width, height))
}

export async function jpegFromBitmap(img: ImageBitmap, maxSide = 800): Promise<{ url: string; blob: Blob }> {
  const scale = Math.min(1, maxSide / Math.max(img.width, img.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(img.width * scale))
  canvas.height = Math.max(1, Math.round(img.height * scale))
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('canvas')
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((value) => (value ? resolve(value) : reject(new Error('blob'))), 'image/jpeg', 0.72)
  })
  return { url: URL.createObjectURL(blob), blob }
}
