// preprocess.ts against a Pillow oracle (scripts/make_preprocess_fixtures.py): the 224 x 224 crop
// must be byte-identical to torchvision Resize(224) + CenterCrop(224) on the same decoded pixels.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import sharp from 'sharp';
import { describe, expect, it } from 'vitest';
import { buildNormLut, centerCropOffsets, preprocess, resizeAndCrop, resizedSize } from '../../src/engine/preprocess';

const APP = resolve(__dirname, '../..');
const ORACLE = JSON.parse(readFileSync(resolve(__dirname, 'fixtures/preprocess_oracle.json'), 'utf8')).sha256_rgb224 as Record<string, string>;

describe('preprocess.ts equals the training eval transform', () => {
  it.each(Object.entries(ORACLE))('%s', async (path, sha) => {
    const { data, info } = await sharp(resolve(APP, path)).removeAlpha().ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    const rgb = resizeAndCrop(new Uint8ClampedArray(data.buffer, data.byteOffset, data.length), info.width, info.height);
    expect(createHash('sha256').update(rgb).digest('hex')).toBe(sha);
  });

  it('sizes and crop offsets follow torchvision', () => {
    expect(resizedSize(640, 480)).toEqual([298, 224]);
    expect(resizedSize(113, 256)).toEqual([224, 507]);
    expect(centerCropOffsets(229, 224)).toEqual({ left: 2, top: 0 }); // round(2.5) = 2
    expect(centerCropOffsets(231, 224)).toEqual({ left: 4, top: 0 }); // round(3.5) = 4
  });

  it('normalises in float32 into NCHW', () => {
    const lut = buildNormLut([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]);
    const px = new Uint8ClampedArray(224 * 224 * 4).fill(128);
    const x = preprocess(px, 224, 224);
    expect(x).toHaveLength(3 * 224 * 224);
    expect(x[0]).toBe(lut[128]);
    expect(x[224 * 224]).toBe(lut[256 + 128]);
    expect(x[2 * 224 * 224]).toBe(lut[512 + 128]);
  });
});
