// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AnswerCard, Check, Label, LeafResult, PlotSummary } from '../../src/engine/types';

const counts = (): Record<Label, number> => ({ healthy: 0, rust: 0, cercospora: 0, phoma: 0, miner: 0, not_leaf: 0 });

const engine = vi.hoisted(() => ({
  loadModel: vi.fn(),
  classifyLeaf: vi.fn(),
  summarisePlot: vi.fn(),
  seasonWindow: vi.fn(),
  decide: vi.fn(),
  saveCheck: vi.fn(),
  getConsent: vi.fn(),
  setConsent: vi.fn(),
  buildReferral: vi.fn(),
}));

vi.mock('../../src/engine', () => engine);

import { _resetEngineHookForTests, useCheck, useConsent, useEngine, useOnline } from '../../src/hooks/useEngine';

const leaf = (label: LeafResult['label'], quality: Partial<LeafResult['quality']> = {}): LeafResult => ({
  label,
  probs: counts(),
  confidence: 0.9,
  quality: { ok: true, blur: 100, brightness: 120, ...quality },
  abstained: label === 'unsure',
  modelVersion: 'mock',
});

const card: AnswerCard = { id: 'rust_high_pre_rains', severity: 'act', text: {}, audio: {}, sources: [], assumption: false };

beforeEach(() => {
  vi.clearAllMocks();
  _resetEngineHookForTests();
  engine.loadModel.mockResolvedValue({ version: 'mock', mock: true });
  engine.summarisePlot.mockImplementation((ls: LeafResult[]): PlotSummary => ({
    n: ls.length,
    counts: { ...counts(), rust: ls.filter((l) => l.label === 'rust').length },
    uncertain: 0,
    dominant: ls.length ? 'rust' : 'none',
    affected: ls.length,
    distinctProblems: ls.length ? 1 : 0,
  }));
  engine.decide.mockReturnValue(card);
  engine.seasonWindow.mockReturnValue('pre_short_rains');
  engine.saveCheck.mockResolvedValue(undefined);
  engine.getConsent.mockResolvedValue({ main: true, photos: false });
  engine.setConsent.mockResolvedValue(undefined);
  engine.buildReferral.mockImplementation((c: Check) => `JANI1 N:${c.summary.n} X:${c.decision ?? '-'}`);
});

// Minimal renderHook: @testing-library/dom (a peer of @testing-library/react) is not installed.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
const roots: Root[] = [];

function renderHook<T>(hook: () => T): { result: { current: T } } {
  const result = { current: undefined as T };
  function Probe() {
    result.current = hook();
    return null;
  }
  const root = createRoot(document.createElement('div'));
  roots.push(root);
  act(() => root.render(<Probe />));
  return { result };
}

async function waitFor(fn: () => void, timeout = 2000): Promise<void> {
  const start = Date.now();
  for (;;) {
    try {
      fn();
      return;
    } catch (e) {
      if (Date.now() - start > timeout) throw e;
      await act(() => new Promise((r) => setTimeout(r, 10)));
    }
  }
}

afterEach(() => {
  for (const r of roots.splice(0)) act(() => r.unmount());
  vi.restoreAllMocks();
});

describe('useOnline', () => {
  it('reacts to online and offline events', () => {
    const spy = vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);
    const { result } = renderHook(() => useOnline());
    expect(result.current).toBe(true);
    spy.mockReturnValue(false);
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    expect(result.current).toBe(false);
    spy.mockReturnValue(true);
    act(() => {
      window.dispatchEvent(new Event('online'));
    });
    expect(result.current).toBe(true);
  });
});

describe('useEngine', () => {
  it('exposes mock and loads the real model once per page', async () => {
    engine.loadModel.mockResolvedValue({ version: 'v1', mock: false });
    const a = renderHook(() => useEngine());
    expect(a.result.current.ready).toBe(false);
    await waitFor(() => expect(a.result.current.ready).toBe(true));
    expect(a.result.current).toEqual({ ready: true, mock: false, version: 'v1', error: null });
    const b = renderHook(() => useEngine());
    expect(b.result.current.ready).toBe(true);
    await act(() => new Promise((r) => setTimeout(r, 10)));
    expect(engine.loadModel).toHaveBeenCalledTimes(1);
  });

  it('asks loadModel again on the next mount after a mock result, and picks up the real model', async () => {
    const a = renderHook(() => useEngine());
    await waitFor(() => expect(a.result.current.ready).toBe(true));
    expect(a.result.current).toEqual({ ready: true, mock: true, version: 'mock', error: null });
    engine.loadModel.mockResolvedValue({ version: 'v1', mock: false });
    const b = renderHook(() => useEngine());
    await waitFor(() => expect(b.result.current.mock).toBe(false));
    expect(b.result.current.version).toBe('v1');
    expect(engine.loadModel).toHaveBeenCalledTimes(2);
  });

  it('reports a load error', async () => {
    engine.loadModel.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useEngine());
    await waitFor(() => expect(result.current.error).toBe('boom'));
    expect(result.current.ready).toBe(false);
  });
});

describe('useConsent', () => {
  it('loads and sets consent', async () => {
    const { result } = renderHook(() => useConsent());
    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.consent).toEqual({ main: true, photos: false });
    await act(() => result.current.setConsent({ main: true, photos: true }));
    expect(engine.setConsent).toHaveBeenCalledWith({ main: true, photos: true });
    expect(result.current.consent).toEqual({ main: true, photos: true });
  });
});

describe('useCheck', () => {
  const img = {} as ImageBitmap;

  it('classify returns retake prompts and does not add the leaf', async () => {
    const { result } = renderHook(() => useCheck());
    engine.classifyLeaf.mockResolvedValueOnce(leaf('unsure', { ok: false, reason: 'dark' }));
    expect((await result.current.classify(img)).retake).toBe('retake_dark');
    engine.classifyLeaf.mockResolvedValueOnce(leaf('unsure', { ok: false, reason: 'too_small' }));
    expect((await result.current.classify(img)).retake).toBe('retake_blurry');
    engine.classifyLeaf.mockResolvedValueOnce(leaf('not_leaf'));
    expect((await result.current.classify(img)).retake).toBe('not_a_leaf');
    engine.classifyLeaf.mockResolvedValueOnce(leaf('unsure', { ok: false, reason: 'not_on_page' }));
    expect((await result.current.classify(img)).retake).toBe('retake_on_page');
    engine.classifyLeaf.mockResolvedValueOnce(leaf('rust'));
    await result.current.classify(img, { sheetGate: false });
    expect(engine.classifyLeaf).toHaveBeenLastCalledWith(img, { sheetGate: false });
    engine.classifyLeaf.mockResolvedValueOnce(leaf('rust'));
    const ok = await result.current.classify(img);
    expect(ok.retake).toBeNull();
    expect(ok.result.label).toBe('rust');
    expect(result.current.leaves).toHaveLength(0);
    expect(result.current.card).toBeNull();
  });

  it('accept, summary, card, decision, save with consent flags, referral, reset', async () => {
    const now = () => new Date(2026, 9, 4, 10, 0);
    const { result } = renderHook(() => useCheck({ lang: 'kik', memberId: 'OCC0412', plotId: 'P07', now }));
    act(() => {
      result.current.accept(leaf('rust'));
      result.current.accept(leaf('rust'));
      result.current.accept(leaf('healthy'));
    });
    expect(result.current.leaves).toHaveLength(3);
    expect(result.current.summary.n).toBe(3);
    expect(result.current.card?.id).toBe('rust_high_pre_rains');
    act(() => result.current.removeLeaf(2));
    expect(result.current.summary.counts.rust).toBe(2);
    expect(result.current.summary.n).toBe(2);
    expect(result.current.referralText()).toBe('JANI1 N:2 X:-');
    act(() => result.current.setDecision('ask'));
    expect(result.current.decision).toBe('ask');

    let saved: Check | undefined;
    await act(async () => {
      saved = await result.current.save();
    });
    expect(engine.saveCheck).toHaveBeenCalledTimes(1);
    const arg = engine.saveCheck.mock.calls[0][0] as Check;
    expect(arg).toBe(saved);
    expect(arg).toMatchObject({
      createdAt: now().toISOString(),
      lang: 'kik',
      window: 'pre_short_rains',
      answerId: 'rust_high_pre_rains',
      decision: 'ask',
      memberId: 'OCC0412',
      plotId: 'P07',
      consentMain: true,
      consentPhotos: false,
      synced: false,
    });
    expect(arg.leaves).toHaveLength(2);
    expect(typeof arg.id).toBe('string');
    expect(arg.id.length).toBeGreaterThan(5);
    expect(result.current.lastCheck).toBe(saved);
    expect(result.current.referralText()).toBe('JANI1 N:2 X:ask');
    expect(engine.buildReferral).toHaveBeenLastCalledWith(saved);

    act(() => result.current.reset());
    expect(result.current.leaves).toHaveLength(0);
    expect(result.current.decision).toBeNull();
    expect(result.current.card).toBeNull();
    expect(result.current.referralText()).toBeNull();
  });

  it('save with no leaves rejects and stores nothing', async () => {
    const { result } = renderHook(() => useCheck());
    await expect(result.current.save()).rejects.toThrow();
    expect(engine.saveCheck).not.toHaveBeenCalled();
  });
});
