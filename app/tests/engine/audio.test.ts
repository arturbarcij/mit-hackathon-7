import { describe, expect, it } from 'vitest';
import { resolveAudioUrl } from '../../src/engine/audio.ts';

describe('resolveAudioUrl', () => {
  it('prefers the requested language, then Swahili, then nothing', () => {
    const existing = new Set(['/audio/sw/healthy_all.mp3', '/audio/en/rust_low.mp3']);
    expect(resolveAudioUrl('rust_low', 'en', existing)).toBe('/audio/en/rust_low.mp3');
    expect(resolveAudioUrl('healthy_all', 'kik', existing)).toBe('/audio/sw/healthy_all.mp3');
    expect(resolveAudioUrl('missing', 'en', existing)).toBeNull();
  });
});
