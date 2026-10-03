import { afterEach, describe, expect, it, vi } from 'vitest';

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe('loadModel', () => {
  it('uses the mock model when VITE_USE_MOCK_MODEL is true, without fetching anything', async () => {
    vi.stubEnv('VITE_USE_MOCK_MODEL', 'true');
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    const { loadModel } = await import('../../src/engine/model');
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('reports the mock (so the UI badge shows) when the real model files are missing', async () => {
    vi.stubEnv('VITE_USE_MOCK_MODEL', 'false');
    vi.stubGlobal('fetch', vi.fn(async () => new Response('not found', { status: 404 })));
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { loadModel } = await import('../../src/engine/model');
    expect(await loadModel()).toEqual({ version: 'mock', mock: true });
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('treats an HTML answer from the dev server as a missing model', async () => {
    vi.stubEnv('VITE_USE_MOCK_MODEL', 'false');
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<!doctype html>', { status: 200 })));
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { loadModel } = await import('../../src/engine/model');
    expect((await loadModel()).mock).toBe(true);
    warn.mockRestore();
  });
});
