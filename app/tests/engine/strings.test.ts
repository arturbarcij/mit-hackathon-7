import { describe, expect, it } from 'vitest';
import { getAnswer } from '../../src/engine/decide';
import { cardText } from '../../src/ui/strings';

// Gate blocker (4 Oct): unreviewed Swahili advice must carry a visible draft tag.
describe('cardText review tags', () => {
  it('tags a Swahili draft card as a draft pending review', () => {
    const c = cardText(getAnswer('rust_high_pre_rains'), 'sw');
    expect(c.shown).toBe('sw');
    expect(c.tag).toBe('Draft, pending review');
  });
  it('tags a Kikuyu machine draft as a machine translation', () => {
    const c = cardText(getAnswer('healthy_all'), 'kik');
    expect(c.shown).toBe('kik');
    expect(c.tag).toBe('Machine translation, pending review');
  });
  it('shows the not translated tag when it falls back to another language', () => {
    expect(cardText(getAnswer('too_few_leaves'), 'kik').tag).toBe('Not translated yet');
  });
  it('shows no tag on English', () => {
    expect(cardText(getAnswer('rust_high_pre_rains'), 'en').tag).toBeNull();
  });
});
