import { describe, expect, it } from 'vitest';
import { calibratedSoftmax, leafResultFromBadQuality, leafResultFromProbs, probsRecord, zeroProbs } from '../../src/engine/scoring';
import { classifyMock, mockProbs, MOCK_THRESHOLD } from '../../src/engine/model.mock';
import { cropRegion, rgbaToTensor } from '../../src/engine/preprocess';
import { parseModelConfig } from '../../src/engine/model';
import { goodQuality } from './helpers';

describe('scoring', () => {
  it('softmax sums to one and is stable for large logits', () => {
    const p = calibratedSoftmax([1000, 999, 0], 1);
    expect(p.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 6);
    expect(p[0]).toBeGreaterThan(p[1]);
    expect(Number.isFinite(p[2])).toBe(true);
  });

  it('a higher temperature flattens the distribution', () => {
    const sharp = calibratedSoftmax([3, 1, 0], 1)[0];
    const soft = calibratedSoftmax([3, 1, 0], 3)[0];
    expect(soft).toBeLessThan(sharp);
  });

  it('treats a bad temperature as 1', () => {
    expect(calibratedSoftmax([1, 2], 0)).toEqual(calibratedSoftmax([1, 2], 1));
    expect(calibratedSoftmax([1, 2], NaN)).toEqual(calibratedSoftmax([1, 2], 1));
  });

  it('abstains below the threshold and commits at or above it', () => {
    const labels = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'] as const;
    const low = leafResultFromProbs(probsRecord(labels, [0.5, 0.3, 0.1, 0.05, 0.03, 0.02]), 0.6, goodQuality, 'v');
    expect(low.label).toBe('unsure');
    expect(low.abstained).toBe(true);
    expect(low.confidence).toBe(0.5);
    const high = leafResultFromProbs(probsRecord(labels, [0.05, 0.8, 0.05, 0.05, 0.03, 0.02]), 0.6, goodQuality, 'v');
    expect(high.label).toBe('rust');
    expect(high.abstained).toBe(false);
    const edge = leafResultFromProbs(probsRecord(labels, [0.1, 0.6, 0.1, 0.1, 0.05, 0.05]), 0.6, goodQuality, 'v');
    expect(edge.label).toBe('rust');
  });

  it('a failed quality gate gives unsure with zero probabilities', () => {
    const r = leafResultFromBadQuality({ ok: false, reason: 'blurry', blur: 1, brightness: 100 }, 'v');
    expect(r.label).toBe('unsure');
    expect(r.abstained).toBe(true);
    expect(r.probs).toEqual(zeroProbs());
  });
});

describe('mock model', () => {
  it('is deterministic by file name', () => {
    expect(mockProbs('rust_01.jpg')).toEqual(mockProbs('rust_01.jpg'));
    expect(classifyMock('IMG_rust_3.jpg', goodQuality)).toMatchObject({ label: 'rust', modelVersion: 'mock' });
    expect(classifyMock('rust.jpg', goodQuality).confidence).toBeCloseTo(0.9, 6);
    expect(classifyMock('cerco.jpg', goodQuality).label).toBe('cercospora');
    expect(classifyMock('miner.jpg', goodQuality).label).toBe('miner');
    expect(classifyMock('phoma.jpg', goodQuality).label).toBe('phoma');
    expect(classifyMock('table.jpg', goodQuality).label).toBe('not_leaf');
    expect(classifyMock('IMG_0001.jpg', goodQuality).label).toBe('healthy');
  });

  it('returns low confidence and abstains for blur', () => {
    const r = classifyMock('blur_2.jpg', goodQuality);
    expect(r.confidence).toBeLessThan(MOCK_THRESHOLD);
    expect(r.label).toBe('unsure');
    expect(r.abstained).toBe(true);
  });

  it('probabilities sum to one', () => {
    for (const name of ['rust', 'blur', 'x', 'table']) {
      const sum = Object.values(mockProbs(name)).reduce((a, b) => a + b, 0);
      expect(sum).toBeCloseTo(1, 6);
    }
  });
});

describe('preprocessing', () => {
  const cfg = { size: 2, resize: 'shorter_side_then_center_crop', mean: [0.5, 0.25, 0] as [number, number, number], std: [0.5, 0.25, 1] as [number, number, number], layout: 'NCHW', range: '0-1' };

  it('writes NCHW with per-channel mean and std', () => {
    const rgba = new Uint8ClampedArray([
      255, 0, 0, 255,   0, 255, 0, 255,
      0, 0, 255, 255,   255, 255, 255, 255,
    ]);
    const t = rgbaToTensor(rgba, 2, cfg);
    expect(t).toHaveLength(12);
    // R plane: (v/255 - 0.5) / 0.5
    expect(Array.from(t.slice(0, 4))).toEqual([1, -1, -1, 1]);
    // G plane: (v/255 - 0.25) / 0.25
    expect(Array.from(t.slice(4, 8))).toEqual([-1, 3, -1, 3]);
    // B plane: (v/255 - 0) / 1
    expect(Array.from(t.slice(8, 12))).toEqual([0, 0, 1, 1]);
  });

  it('crops the centre square of the shorter side', () => {
    expect(cropRegion(400, 300, 224)).toEqual({ sx: 50, sy: 0, side: 300 });
    expect(cropRegion(300, 400, 224)).toEqual({ sx: 0, sy: 50, side: 300 });
  });

  it('crops 224/256 of the shorter side when resize_to is given', () => {
    const r = cropRegion(512, 512, 224, 256);
    expect(r.side).toBe(448);
    expect(r.sx).toBe(32);
  });
});

describe('model.json parsing', () => {
  const good = {
    version: 'v1', labels: ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'],
    input: { size: 224, resize: 'shorter_side_then_center_crop', mean: [0.485, 0.456, 0.406], std: [0.229, 0.224, 0.225], layout: 'NCHW', range: '0-1' },
    temperature: 1.2, threshold: 0.7, sha256: '', bytes: 0,
  };
  it('accepts the documented shape', () => {
    expect(parseModelConfig(good).threshold).toBe(0.7);
  });
  it('rejects malformed config', () => {
    expect(() => parseModelConfig({})).toThrow();
    expect(() => parseModelConfig({ ...good, labels: ['healthy', 'banana'] })).toThrow();
    expect(() => parseModelConfig({ ...good, temperature: 'hot' })).toThrow();
    expect(() => parseModelConfig(null)).toThrow();
  });
});
