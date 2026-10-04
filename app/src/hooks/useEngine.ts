// React hooks the UI calls. Thin wrappers over the engine; nothing here sends anything.
// SSR-safe: window, navigator and crypto are only read inside effects and callbacks.
//
// Usage (for the ui agent):
//
//   const { ready, mock } = useEngine();            // show a "mock model" badge when mock is true
//   const online = useOnline();
//   const { consent, loading, setConsent } = useConsent();
//   const chk = useCheck({ lang: 'sw', memberId: 'OCC0412', plotId: 'P07' });
//
//   // Photo taken: the File from <input type="file" capture> (decoded at native size), or an ImageBitmap:
//   const { result, retake } = await chk.classify(bitmap);
//   if (retake) showAnswer(retake);                 // 'retake_blurry' | 'retake_dark' | 'retake_on_page' | 'not_a_leaf'
//   // Bundled demo photos are not on a page: chk.classify(bitmap, { sheetGate: false }) for those only.
//   else chk.accept(result);                        // adds the leaf
//
//   chk.leaves, chk.summary, chk.card               // card is null until one leaf is accepted
//   chk.setDecision('ask');                         // Noor taps act / wait / ask
//   const saved = await chk.save();                 // stores the Check on the phone
//   const body = chk.referralText();                // JANI1 SMS body, or null with no leaves
//   if (body) location.href = smsLink(coopNumber, body); // only on a user tap
//   chk.reset();
import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import {
  buildReferral,
  classifyLeaf,
  decide,
  getConsent,
  loadModel,
  saveCheck,
  seasonWindow,
  setConsent as engineSetConsent,
  summarisePlot,
} from '../engine';
import type {
  AnswerCard,
  Check,
  ClassifyOptions,
  Consent,
  Decision,
  ImageInput,
  Lang,
  LeafResult,
  ModelInfo,
  PlotSummary,
} from '../engine';

// ---- useEngine ----

let modelPromise: Promise<ModelInfo> | null = null;
let modelInfo: ModelInfo | null = null;
let modelError: string | null = null;

function ensureModel(): Promise<ModelInfo> {
  if (!modelPromise) {
    modelPromise = loadModel().then(
      (info) => {
        modelInfo = info;
        // loadModel caches only settled outcomes; a mock result may be a transient failure,
        // so the next mount asks again (cheap when loadModel has it cached).
        if (info.mock) modelPromise = null;
        return info;
      },
      (e: unknown) => {
        modelError = e instanceof Error ? e.message : String(e);
        throw e;
      },
    );
  }
  return modelPromise;
}

/** Test hook: forget the page-level model promise. */
export function _resetEngineHookForTests(): void {
  modelPromise = null;
  modelInfo = null;
  modelError = null;
}

export interface EngineState {
  ready: boolean;
  mock: boolean;
  version: string | null;
  error: string | null;
}

function engineState(): EngineState {
  return {
    ready: modelInfo !== null,
    mock: modelInfo?.mock ?? false,
    version: modelInfo?.version ?? null,
    error: modelError,
  };
}

/** Loads the model once per page and reports its state. */
export function useEngine(): EngineState {
  const [state, setState] = useState<EngineState>(engineState);
  useEffect(() => {
    let live = true;
    ensureModel().then(
      () => live && setState(engineState()),
      () => live && setState(engineState()),
    );
    return () => {
      live = false;
    };
  }, []);
  return state;
}

// ---- useOnline ----

function subscribeOnline(cb: () => void): () => void {
  if (typeof window === 'undefined') return () => {};
  window.addEventListener('online', cb);
  window.addEventListener('offline', cb);
  return () => {
    window.removeEventListener('online', cb);
    window.removeEventListener('offline', cb);
  };
}

export function useOnline(): boolean {
  return useSyncExternalStore(
    subscribeOnline,
    () => (typeof navigator === 'undefined' ? true : navigator.onLine !== false),
    () => true,
  );
}

// ---- useConsent ----

export interface ConsentState {
  consent: Consent | null;
  loading: boolean;
  setConsent: (c: Consent) => Promise<void>;
}

export function useConsent(): ConsentState {
  const [consent, setLocal] = useState<Consent | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    getConsent().then(
      (c) => {
        if (!live) return;
        setLocal(c);
        setLoading(false);
      },
      () => live && setLoading(false),
    );
    return () => {
      live = false;
    };
  }, []);
  const setConsent = useCallback(async (c: Consent) => {
    await engineSetConsent(c);
    setLocal(c);
  }, []);
  return { consent, loading, setConsent };
}

// ---- useCheck ----

export type Retake = 'retake_blurry' | 'retake_dark' | 'retake_on_page' | 'not_a_leaf';

export interface ClassifyOutcome {
  result: LeafResult;
  retake: Retake | null;
}

export interface CheckOptions {
  lang?: Lang;
  memberId?: string;
  plotId?: string;
  now?: () => Date;
}

export interface CheckState {
  leaves: LeafResult[];
  decision: Decision | null;
  summary: PlotSummary;
  card: AnswerCard | null;
  lastCheck: Check | null;
  classify: (img: ImageInput | Blob, opts?: ClassifyOptions) => Promise<ClassifyOutcome>;
  accept: (result: LeafResult) => void;
  removeLeaf: (index: number) => void;
  setDecision: (d: Decision | null) => void;
  save: () => Promise<Check>;
  referralText: () => string | null;
  reset: () => void;
}

/** Which retake prompt a classified photo needs, if any. */
export function retakeFor(r: LeafResult): Retake | null {
  if (r.quality && !r.quality.ok) {
    if (r.quality.reason === 'dark') return 'retake_dark';
    if (r.quality.reason === 'not_on_page') return 'retake_on_page';
    return 'retake_blurry';
  }
  if (r.label === 'not_leaf') return 'not_a_leaf';
  return null;
}

function newId(): string {
  const c = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined;
  if (c && typeof c.randomUUID === 'function') return c.randomUUID();
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function useCheck(opts: CheckOptions = {}): CheckState {
  const { lang = 'sw', memberId, plotId } = opts;
  const now = opts.now;
  const [leaves, setLeaves] = useState<LeafResult[]>([]);
  const [decision, setDecisionState] = useState<Decision | null>(null);
  const [lastCheck, setLastCheck] = useState<Check | null>(null);

  const summary = useMemo(() => summarisePlot(leaves), [leaves]);
  const card = useMemo(
    () => (leaves.length > 0 ? decide(summary, now ? now() : new Date()) : null),
    [summary, leaves.length, now],
  );

  const classify = useCallback(async (img: ImageInput | Blob, opts?: ClassifyOptions): Promise<ClassifyOutcome> => {
    const result = await classifyLeaf(img, opts);
    return { result, retake: retakeFor(result) };
  }, []);

  const accept = useCallback((result: LeafResult) => {
    setLeaves((prev) => [...prev, result]);
    setLastCheck(null);
  }, []);

  const removeLeaf = useCallback((index: number) => {
    setLeaves((prev) => prev.filter((_, i) => i !== index));
    setLastCheck(null);
  }, []);

  const setDecision = useCallback((d: Decision | null) => {
    setDecisionState(d);
    setLastCheck(null);
  }, []);

  const buildCheck = useCallback(
    (consent: Consent): Check => {
      const date = now ? now() : new Date();
      const s = summarisePlot(leaves);
      return {
        id: newId(),
        createdAt: date.toISOString(),
        lang,
        leaves,
        summary: s,
        window: seasonWindow(date),
        answerId: decide(s, date).id,
        ...(decision ? { decision } : {}),
        ...(memberId ? { memberId } : {}),
        ...(plotId ? { plotId } : {}),
        consentMain: consent.main,
        consentPhotos: consent.photos,
        synced: false,
      };
    },
    [leaves, decision, lang, memberId, plotId, now],
  );

  const save = useCallback(async (): Promise<Check> => {
    if (leaves.length === 0) throw new Error('Jani: no leaves to save');
    const consent = await getConsent();
    const check = buildCheck(consent);
    await saveCheck(check);
    setLastCheck(check);
    return check;
  }, [leaves.length, buildCheck]);

  const referralText = useCallback((): string | null => {
    if (lastCheck) return buildReferral(lastCheck);
    if (leaves.length === 0) return null;
    return buildReferral(buildCheck({ main: false, photos: false }));
  }, [lastCheck, leaves.length, buildCheck]);

  const reset = useCallback(() => {
    setLeaves([]);
    setDecisionState(null);
    setLastCheck(null);
  }, []);

  return { leaves, decision, summary, card, lastCheck, classify, accept, removeLeaf, setDecision, save, referralText, reset };
}
