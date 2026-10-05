import { afterEach, describe, expect, it, vi } from 'vitest';
import { audioFallbackChain, audioUrl, play } from '../../src/engine/audio';

type Listener = () => void;

function stubAudio(existing: (url: string) => boolean, blocked = false) {
  const tried: string[] = [];
  class FakeAudio {
    listeners: Record<string, Listener> = {};
    constructor(public url: string) {
      tried.push(url);
    }
    addEventListener(name: string, fn: Listener) {
      this.listeners[name] = fn;
    }
    pause() {
      this.listeners.pause?.();
    }
    play() {
      if (blocked) return Promise.reject(Object.assign(new Error('x'), { name: 'NotAllowedError' }));
      queueMicrotask(() => (existing(this.url) ? this.listeners.ended?.() : this.listeners.error?.()));
      return Promise.resolve();
    }
  }
  vi.stubGlobal('Audio', FakeAudio);
  return tried;
}

afterEach(() => vi.unstubAllGlobals());

describe('audio', () => {
  it('builds the clip path', () => {
    expect(audioUrl('rust_low', 'kik')).toMatch(/audio\/kik\/rust_low\.mp3$/);
  });

  it('falls back from the chosen language to Swahili only', () => {
    expect(audioFallbackChain('kik')).toEqual(['kik', 'sw']);
    expect(audioFallbackChain('en')).toEqual(['en', 'sw']);
    expect(audioFallbackChain('sw')).toEqual(['sw']);
  });

  it('plays the chosen language when it exists', async () => {
    const tried = stubAudio(() => true);
    await play('rust_low', 'kik');
    expect(tried).toHaveLength(1);
    expect(tried[0]).toContain('/kik/');
  });

  it('falls back to Swahili when the clip is missing', async () => {
    const tried = stubAudio((u) => u.includes('/sw/'));
    await play('rust_low', 'kik');
    expect(tried.map((u) => u.split('/').at(-2))).toEqual(['kik', 'sw']);
  });

  it('resolves quietly when no clip exists', async () => {
    const tried = stubAudio(() => false);
    await expect(play('rust_low', 'en')).resolves.toBeUndefined();
    expect(tried).toHaveLength(2);
  });

  it('does not try other languages when the browser blocks autoplay', async () => {
    const tried = stubAudio(() => true, true);
    await expect(play('rust_low', 'kik')).resolves.toBeUndefined();
    expect(tried).toHaveLength(1);
  });

  it('resolves quietly when there is no Audio support', async () => {
    vi.stubGlobal('Audio', undefined);
    await expect(play('x', 'sw')).resolves.toBeUndefined();
  });
});
