// smsLink(number, body): Android uses '?body=', iOS uses '&body='. The body is percent-encoded.
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as engine from '@engine';

const smsLink = (engine as any).smsLink as (n: string, b: string) => string;
const ANDROID = 'Mozilla/5.0 (Linux; Android 10; TECNO KE5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36';
const IOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
const BODY = 'JANI1 M:OCC0412 P:2 D:20261004 N:10 R:6 C:0 H:0 L:1 U:1 A:rust_high_pre_rains Q:87 X:ask';
const as = (ua: string) => vi.stubGlobal('navigator', { userAgent: ua, onLine: true });
const bodyOf = (link: string) => decodeURIComponent(link.slice(link.indexOf('body=') + 5));

afterEach(() => vi.unstubAllGlobals());

describe('smsLink', () => {
  it('is exported', () => expect(typeof smsLink).toBe('function'));

  it('Android: sms:<number>?body=<encoded>', () => {
    as(ANDROID);
    const link = smsLink('+254700123456', BODY);
    expect(link.startsWith('sms:+254700123456?body=')).toBe(true);
    expect(bodyOf(link)).toBe(BODY);
  });

  it('iOS: sms:<number>&body=<encoded>', () => {
    as(IOS);
    const link = smsLink('+254700123456', BODY);
    expect(link.startsWith('sms:+254700123456&body=')).toBe(true);
    expect(bodyOf(link)).toBe(BODY);
  });

  it('encodes spaces as %20 (not +) and reserved characters in the body', () => {
    as(ANDROID);
    const body = 'a b&c?d#e+f%g=h';
    const link = smsLink('0700123456', body);
    const enc = link.slice(link.indexOf('body=') + 5);
    expect(enc).not.toMatch(/[ &?#+]/);
    expect(enc).toContain('%20');
    expect(bodyOf(link)).toBe(body);
  });

  it('keeps a leading + on the number (international format)', () => {
    as(ANDROID);
    expect(smsLink('+254700123456', 'x')).toMatch(/^sms:\+254700123456\?/);
  });

  it('a number typed with spaces gives a link with no raw spaces', () => {
    as(ANDROID);
    expect(smsLink('0700 123 456', BODY)).not.toMatch(/\s/);
  });

  it('builds a link only; it does not navigate or open anything', () => {
    const open = vi.fn();
    vi.stubGlobal('window', { open, location: { href: 'about:blank' } });
    as(ANDROID);
    smsLink('0700123456', BODY);
    expect(open).not.toHaveBeenCalled();
    expect((globalThis as any).window.location.href).toBe('about:blank');
  });
});
