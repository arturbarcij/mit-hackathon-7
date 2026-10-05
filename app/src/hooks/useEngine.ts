import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  assembleCheck,
  buildReferral,
  classifyFile,
  decide,
  getConsent,
  loadModel,
  newId,
  saveCheck,
  setConsent,
  smsLink,
  summarisePlot,
  syncPending,
} from '../engine';
import type { AnswerCard, Check, Consent, Decision, Lang, LeafResult, PlotSummary } from '../engine';

export type ModelStatus = 'loading' | 'ready' | 'error';

/** Loads the model once. `mock` is true when the mock model is active; the UI must show a visible badge. */
export function useEngine() {
  const [status, setStatus] = useState<ModelStatus>('loading');
  const [mock, setMock] = useState(false);
  const [version, setVersion] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    loadModel()
      .then((m) => {
        if (!alive) return;
        setMock(m.mock);
        setVersion(m.version);
        setStatus('ready');
      })
      .catch((e: unknown) => {
        if (!alive) return;
        setError(e instanceof Error ? e.message : String(e));
        setStatus('error');
      });
    return () => {
      alive = false;
    };
  }, []);

  const online = typeof navigator === 'undefined' ? true : navigator.onLine;
  const model = { ready: status === 'ready', mock, version, error };
  return { status, ready: status === 'ready', mock, version, error, online, model };
}

export interface PhotoOutcome {
  /** False when the quality gate failed. The photo was not added; ask for a retake. */
  accepted: boolean;
  result: LeafResult;
}

export interface UseCheckOptions {
  lang: Lang;
  memberId?: string;
  plotId?: string;
  /** Target number of leaves. Default 10. */
  target?: number;
}

/**
 * One leaf check from first photo to saved decision.
 * Photos that fail the quality gate are not added. Leaves the model is unsure about are added and counted as uncertain.
 * Nothing is saved or sent until `choose` is called with the farmer's decision.
 */
export function useCheck(opts: UseCheckOptions) {
  const { lang, memberId, plotId } = opts;
  const target = opts.target ?? 10;
  const [leaves, setLeaves] = useState<LeafResult[]>([]);
  const [photos, setPhotos] = useState<Blob[]>([]);
  const [busy, setBusy] = useState(false);
  const [decision, setDecision] = useState<Decision | undefined>(undefined);
  const [saved, setSaved] = useState<Check | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [checkId, setCheckId] = useState(newId);

  const addPhoto = useCallback(async (file: File | Blob, replaceIndex?: number): Promise<PhotoOutcome> => {
    setBusy(true);
    try {
      const result = await classifyFile(file);
      if (!result.quality.ok) return { accepted: false, result };
      setStartedAt((d) => d ?? new Date());
      setLeaves((prev) => {
        const next = [...prev];
        if (replaceIndex !== undefined && replaceIndex < next.length) next[replaceIndex] = result;
        else next.push(result);
        return next;
      });
      setPhotos((prev) => {
        const next = [...prev];
        if (replaceIndex !== undefined && replaceIndex < next.length) next[replaceIndex] = file;
        else next.push(file);
        return next;
      });
      return { accepted: true, result };
    } finally {
      setBusy(false);
    }
  }, []);

  const summary: PlotSummary = useMemo(() => summarisePlot(leaves), [leaves]);
  const card: AnswerCard | null = useMemo(
    () => (startedAt ? decide(summary, startedAt) : null),
    [startedAt, summary],
  );

  const check: Check | null = useMemo(() => {
    if (leaves.length === 0 || !startedAt) return null;
    const c = assembleCheck({
      leaves,
      lang,
      date: startedAt,
      memberId,
      plotId,
      consentMain: false,
      consentPhotos: false,
    });
    return { ...c, id: checkId, decision };
  }, [leaves, lang, memberId, plotId, decision, startedAt, checkId]);

  /** Records the farmer's own choice and saves the check on the phone. Never sends anything. */
  const choose = useCallback(
    async (d: Decision): Promise<Check | null> => {
      if (!check) return null;
      const consent = await getConsent();
      const final: Check = { ...check, decision: d, consentMain: consent.main, consentPhotos: consent.photos };
      // The decision stands even if the phone cannot store it (private mode, full disk); the UI can tell her.
      try {
        await saveCheck(final, consent.main ? photos : undefined);
        setSaveError(null);
      } catch (e) {
        setSaveError(e instanceof Error ? e.message : String(e));
      }
      setDecision(d);
      setSaved(final);
      return final;
    },
    [check, photos],
  );

  const referralText = useMemo(() => (check ? buildReferral({ ...check, decision: decision ?? 'ask' }) : null), [check, decision]);

  const smsHref = useCallback(
    (number: string) => (referralText ? smsLink(number, referralText) : null),
    [referralText],
  );

  const reset = useCallback(() => {
    setLeaves([]);
    setPhotos([]);
    setDecision(undefined);
    setSaved(null);
    setSaveError(null);
    setStartedAt(null);
    setCheckId(newId());
  }, []);

  const removeLeaf = useCallback((index: number) => {
    setLeaves((p) => p.filter((_, i) => i !== index));
    setPhotos((p) => p.filter((_, i) => i !== index));
  }, []);

  return {
    leaves,
    photos,
    count: leaves.length,
    target,
    complete: leaves.length >= target,
    busy,
    summary,
    card,
    check,
    decision,
    saved,
    saveError,
    referralText,
    smsHref,
    addPhoto,
    retake: (index: number, file: File | Blob) => addPhoto(file, index),
    removeLeaf,
    choose,
    reset,
  };
}

export function useConsent() {
  const [consent, setLocal] = useState<Consent>({ main: false, photos: false });
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let alive = true;
    getConsent().then((c) => {
      if (alive) {
        setLocal(c);
        setLoaded(true);
      }
    });
    return () => {
      alive = false;
    };
  }, []);

  const update = useCallback(async (next: Consent) => {
    await setConsent(next);
    setLocal(await getConsent());
  }, []);

  return {
    consent,
    loaded,
    setMain: (main: boolean) => update({ main, photos: main ? consent.photos : false }),
    setPhotos: (photos: boolean) => update({ main: consent.main, photos }),
  };
}

export function useOnline() {
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);
  return online;
}

export { syncPending };
