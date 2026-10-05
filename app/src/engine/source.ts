const names = new WeakMap<object, string>();

/** The mock model picks its answer from the original file name; the real model ignores it. */
export function nameOf(img: ImageBitmap): string {
  return names.get(img) ?? '';
}

export function rememberName(img: ImageBitmap, name: string): void {
  names.set(img, name);
}

/**
 * Decodes a photo from the camera or file picker. Large photos are decoded at reduced size to
 * keep memory low on cheap phones; 1600 px on the longer side is far more than the model needs.
 */
export async function bitmapFromFile(file: File | Blob, maxSide = 1600): Promise<ImageBitmap> {
  const probe = await createImageBitmap(file);
  const longer = Math.max(probe.width, probe.height);
  let bitmap = probe;
  if (longer > maxSide) {
    const scale = maxSide / longer;
    bitmap = await createImageBitmap(probe, {
      resizeWidth: Math.round(probe.width * scale),
      resizeHeight: Math.round(probe.height * scale),
      resizeQuality: 'high',
    });
    probe.close();
  }
  rememberName(bitmap, (file as File).name ?? '');
  return bitmap;
}
