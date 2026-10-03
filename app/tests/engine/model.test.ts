import { describe, expect, it } from 'vitest';
import { classifyLeaf, loadModel } from '../../src/engine/model.ts';
import { setMockHint } from '../../src/engine/model.mock.ts';
import { classifyPrepared, interpretLogits, type ModelFile } from '../../src/engine/model.ts';
import { imageToNchw } from '../../src/engine/preprocess.ts';
import { LABELS } from '../../src/engine/types.ts';

const spec = {
  size: 224,
  mean: [0.485, 0.456, 0.406],
  std: [0.229, 0.224, 0.225],
};

const config: ModelFile = {
  version: 'fake',
  labels: [...LABELS],
  input: { ...spec, resize: 'shorter_side_then_center_crop', layout: 'NCHW', range: '0-1' },
  temperature: 1,
  threshold: 0.5,
};

function sumProbs(probs: Record<string, number>): number {
  return Object.values(probs).reduce((sum, value) => sum + value, 0);
}

describe('mock model', () => {
  it('loads in mock mode by default', async () => {
    const loaded = await loadModel();
    expect(loaded.mock).toBe(true);
    expect(loaded.version).toBe('mock');
  });

  it('labels a rust hint as rust and does not abstain', async () => {
    const result = await classifyLeaf({ width: 224, height: 224 } as ImageBitmap, { hint: 'leaf_rust.jpg' });
    expect(result.label).toBe('rust');
    expect(result.abstained).toBe(false);
    expect(result.modelVersion).toBe('mock');
    expect(result.confidence).toBeCloseTo(0.9, 5);
    expect(sumProbs(result.probs)).toBeCloseTo(1, 5);
    const fromName = await classifyLeaf({} as ImageBitmap, 'plot-rust.jpg');
    expect(fromName.label).toBe('rust');
    expect(fromName.abstained).toBe(false);
  });

  it('reads the module hint when no option is passed', async () => {
    setMockHint('healthy');
    const result = await classifyLeaf({} as ImageBitmap);
    expect(result.label).toBe('healthy');
    expect(result.abstained).toBe(false);
    setMockHint('');
  });

  it('abstains on a blur hint', async () => {
    const result = await classifyLeaf({} as ImageBitmap, { hint: 'blurry-leaf' });
    expect(result.abstained).toBe(true);
    expect(result.label).toBe('unsure');
    expect(result.quality.ok).toBe(false);
    expect(result.quality.reason).toBe('blurry');
    expect(sumProbs(result.probs)).toBeCloseTo(1, 5);
  });
});

describe('real model head', () => {
  it('uses a fake session and abstains below the threshold', async () => {
    const accepted = await classifyPrepared(new Float32Array(3 * 224 * 224), {
      async run() {
        return { logits: { data: new Float32Array([0, 4, 0, 0, 0, 0]) } };
      },
    }, config);
    expect(accepted.label).toBe('rust');
    expect(accepted.abstained).toBe(false);
    expect(sumProbs(accepted.probs)).toBeCloseTo(1, 5);

    const rejected = interpretLogits(new Float32Array([0, 0, 0, 0, 0, 0]), config);
    expect(rejected.label).toBe('unsure');
    expect(rejected.abstained).toBe(true);
    expect(rejected.confidence).toBeLessThan(0.5);
  });

  it('normalises a solid red image to ImageNet NCHW', () => {
    const width = 8;
    const height = 16;
    const data = new Uint8ClampedArray(width * height * 4);
    for (let i = 0; i < width * height; i++) {
      data[i * 4] = 255;
      data[i * 4 + 3] = 255;
    }
    const nchw = imageToNchw({ data, width, height }, spec);
    expect(nchw.length).toBe(3 * 224 * 224);
    expect(nchw[0]).toBeCloseTo((1 - 0.485) / 0.229, 5);
    expect(nchw[224 * 224]).toBeCloseTo((0 - 0.456) / 0.224, 5);
    expect(nchw[2 * 224 * 224]).toBeCloseTo((0 - 0.406) / 0.225, 5);
  });
});
