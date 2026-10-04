// Single import point for the engine under test. vitest.config.ts maps
// '@engine-under-test' to ENGINE_PATH (default ../reference). Tests import from
// here only, never from the reference or from Lovable directly.
//
// The module is typed loosely on purpose: a drifted engine must still load so
// that each test can report its own failure. types.test.ts does the strict,
// compile-time signature check.
import * as engine from '@engine-under-test';
import type { AnswerCard, Check, LeafResult, ParsedReferral, PlotSummary, SeasonWindow } from '../reference/types';

declare const __ENGINE_PATH__: string;
export const ENGINE_PATH: string = typeof __ENGINE_PATH__ === 'string' ? __ENGINE_PATH__ : 'reference';

export interface EngineUnderTest {
  summarisePlot?: (leaves: LeafResult[]) => PlotSummary;
  seasonWindow?: (date: Date) => SeasonWindow;
  decide?: (summary: PlotSummary, date: Date) => AnswerCard;
  buildReferral?: (c: Check) => string;
  parseReferral?: (text: string) => ParsedReferral | null;
  smsLink?: (number: string, body: string) => string;
  play?: (answerId: string, lang: string) => Promise<void>;
  [k: string]: unknown;
}

export const e = engine as unknown as EngineUnderTest;

/**
 * The engine's function, or a stub that throws a clear message when called, so
 * each test that needs a missing export fails on its own instead of taking the
 * whole file down.
 */
export function need<K extends keyof EngineUnderTest>(name: K): NonNullable<EngineUnderTest[K]> {
  const fn = e[name];
  if (typeof fn !== 'function') {
    const stub = () => { throw new Error(`engine at ${ENGINE_PATH} does not export ${String(name)}()`); };
    return stub as unknown as NonNullable<EngineUnderTest[K]>;
  }
  return fn as NonNullable<EngineUnderTest[K]>;
}
