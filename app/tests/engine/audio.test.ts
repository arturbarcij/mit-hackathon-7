import { afterEach, describe, expect, it } from 'vitest';
import { _setAudioFactory, audioPath, play, stop, type AudioLike } from '../../src/engine/audio';

type Mode = 'ok' | 'error' | 'reject' | 'hang';

function fakeFactory(modes: Record<string, Mode>) {
  const tried: string[] = [];
  const els: FakeAudio[] = [];
  class FakeAudio implements AudioLike {
    onended: ((ev: Event) => unknown) | null = null;
    onerror: ((ev: Event) => unknown) | null = null;
    paused = false;
    src: string;
    constructor(src: string) {
      this.src = src;
    }
    play(): Promise<void> {
      const mode = modes[this.src] ?? 'error';
      if (mode === 'reject') return Promise.reject(new Error('NotAllowedError'));
      if (mode === 'hang') return Promise.resolve();
      setTimeout(() => (mode === 'ok' ? this.onended : this.onerror)?.(new Event(mode)), 1);
      return Promise.resolve();
    }
    pause() {
      this.paused = true;
    }
  }
  _setAudioFactory((src) => {
    tried.push(src);
    const el = new FakeAudio(src);
    els.push(el);
    return el;
  });
  return { tried, els };
}

afterEach(() => {
  stop();
  _setAudioFactory(null);
});

describe('audio', () => {
  it('builds the clip path', () => {
    expect(audioPath('rust_low', 'kik')).toBe('/audio/kik/rust_low.mp3');
  });

  it('plays the requested language when it exists', async () => {
    const { tried } = fakeFactory({ '/audio/kik/rust_low.mp3': 'ok' });
    await play('rust_low', 'kik');
    expect(tried).toEqual(['/audio/kik/rust_low.mp3']);
  });

  it('falls back to Swahili on a load error', async () => {
    const { tried } = fakeFactory({ '/audio/sw/rust_low.mp3': 'ok' });
    await play('rust_low', 'kik');
    expect(tried).toEqual(['/audio/kik/rust_low.mp3', '/audio/sw/rust_low.mp3']);
  });

  it('falls back to Swahili when play() rejects, then resolves silently', async () => {
    const { tried } = fakeFactory({ '/audio/en/x.mp3': 'reject', '/audio/sw/x.mp3': 'reject' });
    await expect(play('x', 'en')).resolves.toBeUndefined();
    expect(tried).toEqual(['/audio/en/x.mp3', '/audio/sw/x.mp3']);
  });

  it('does not retry Swahili twice', async () => {
    const { tried } = fakeFactory({});
    await play('x', 'sw');
    expect(tried).toEqual(['/audio/sw/x.mp3']);
  });

  it('resolves quietly when the factory throws', async () => {
    _setAudioFactory(() => {
      throw new Error('no audio');
    });
    await expect(play('x', 'kik')).resolves.toBeUndefined();
  });

  it('stop() pauses and resolves the pending play; a new play stops the old one', async () => {
    const { els, tried } = fakeFactory({ '/audio/sw/a.mp3': 'hang', '/audio/sw/b.mp3': 'ok' });
    const first = play('a', 'sw');
    await Promise.resolve();
    const second = play('b', 'sw');
    await first;
    expect(els[0].paused).toBe(true);
    await second;
    expect(tried).toEqual(['/audio/sw/a.mp3', '/audio/sw/b.mp3']);
    const third = play('a', 'sw');
    stop();
    await expect(third).resolves.toBeUndefined();
  });

  it('resolves at once when Audio does not exist (SSR)', async () => {
    expect(typeof (globalThis as { Audio?: unknown }).Audio).toBe('undefined');
    await expect(play('x', 'kik')).resolves.toBeUndefined();
  });
});
