// Compile-time conformance. Not run by vitest directly; types.test.ts runs tsc on
// this file with '@engine-under-test' mapped to the engine. If a signature drifts
// from kb/CONTRACTS.md, tsc fails and so does the suite.
import * as engine from '@engine-under-test';
import type * as C from '../reference/types';

// Every exported function must be assignable to its CONTRACTS signature.
// Only the pure, DOM-free functions are required here; the browser ones are
// checked when present (an engine that omits them fails too, see below).
const summarisePlot: (leaves: C.LeafResult[]) => C.PlotSummary = engine.summarisePlot;
const seasonWindow: (date: Date) => C.SeasonWindow = engine.seasonWindow;
const decide: (summary: C.PlotSummary, date: Date) => C.AnswerCard = engine.decide;
const buildReferral: (c: C.Check) => string = engine.buildReferral;
const smsLink: (number: string, body: string) => string = engine.smsLink;
const parseReferral: (text: string) => C.ParsedReferral | null = engine.parseReferral;

// Types the UI imports from the engine must exist with the CONTRACTS shape.
type AssertSame<A, B> = [A] extends [B] ? ([B] extends [A] ? true : never) : never;
const _lang: AssertSame<engine.Lang, C.Lang> = true;
const _label: AssertSame<engine.Label, C.Label> = true;
const _decision: AssertSame<engine.Decision, C.Decision> = true;
const _leaf: AssertSame<engine.LeafResult, C.LeafResult> = true;
const _summary: AssertSame<engine.PlotSummary, C.PlotSummary> = true;
const _card: AssertSame<engine.AnswerCard, C.AnswerCard> = true;
const _season: AssertSame<engine.SeasonWindow, C.SeasonWindow> = true;
const _check: AssertSame<engine.Check, C.Check> = true;

export { summarisePlot, seasonWindow, decide, buildReferral, smsLink, parseReferral, _lang, _label, _decision, _leaf, _summary, _card, _season, _check };
