// Jani farmer flow, one action per screen (MASTER_PROMPT section 4):
// language -> consent -> how to pick -> how to photograph -> capture (up to 10, retake prompts)
// -> plot summary -> answer card -> decision (act / wait / ask) -> referral SMS or done -> history.
// Everything the farmer reads comes from answers.json through the engine. Nothing is sent
// automatically: the SMS app opens only when the farmer taps Send.
import { useCallback, useEffect, useRef, useState } from 'react';
import { compressPhoto, savePhoto, type Decision, type Lang, type LeafResult } from './engine';
import { useCheck, useConsent, type EngineState } from './hooks/useEngine';
import { EngineProbe } from './components/EngineProbe';
import { TopBar } from './components/Parts';
import { LanguagePage } from './pages/Language';
import { ConsentPage, StoppedPage } from './pages/Consent';
import { GuidePage } from './pages/Guide';
import { CapturePage, MAX_LEAVES, RetakePage, type Rejected } from './pages/Capture';
import { AnswerPage, DecisionPage, SummaryPage } from './pages/Result';
import { DonePage, HistoryPage, ReferralPage } from './pages/After';
import { FarmPage } from './pages/Farm';
import { blockPlotId, FARM_ID } from './ui/farm';
import { classifyPhoto, decodeFile, photoHash, loadSampleManifest, loadSamplePhotos, retakeId, type Photo, type SampleItem } from './ui/photos';
import { registerOffline } from './ui/offline';
import { t } from './ui/strings';
import { stopVoice } from './ui/voice';

type ScreenId =
  | 'language'
  | 'consent'
  | 'stopped'
  | 'pick'
  | 'photo'
  | 'capture'
  | 'retake'
  | 'summary'
  | 'answer'
  | 'decision'
  | 'referral'
  | 'done'
  | 'history'
  | 'farm';

// Demo identity for the referral SMS (synthetic member and plot from public/geo, no names).
const DEMO_MEMBER = 'OCC0412';
// Each coffee block on the My farm map has its own plot ID ("P07-C1"), so checks and referrals say which rows.
const DEMO_PLOT = FARM_ID;

function readLang(): Lang | null {
  try {
    const v = localStorage.getItem('jani.lang');
    return v === 'sw' || v === 'kik' || v === 'en' ? v : null;
  } catch {
    return null;
  }
}

function storeLang(l: Lang): void {
  try {
    localStorage.setItem('jani.lang', l);
  } catch {
    // per-viewer convenience only
  }
}

export default function App() {
  const [engine, setEngine] = useState<EngineState>({ ready: false, mock: false, version: null, error: null });
  const { consent, setConsent } = useConsent();
  const [lang, setLang] = useState<Lang>(() => readLang() ?? 'sw');
  const [screen, setScreen] = useState<ScreenId>('language');
  const [trail, setTrail] = useState<ScreenId[]>([]);
  const [block, setBlock] = useState<string | null>(null);
  const [farmMode, setFarmMode] = useState<'pick' | 'overview'>('pick');
  const [farmNext, setFarmNext] = useState<'photo' | 'capture'>('photo');
  const chk = useCheck({ lang, memberId: DEMO_MEMBER, plotId: block ? blockPlotId(block) : DEMO_PLOT });
  const [accepted, setAccepted] = useState<Photo[]>([]);
  const [rejected, setRejected] = useState<Rejected[]>([]);
  const [current, setCurrent] = useState<Rejected | null>(null);
  const [replacing, setReplacing] = useState<number | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [credits, setCredits] = useState<SampleItem[] | null>(null);
  const [offline, setOffline] = useState<'ready' | 'pending' | 'none'>(() =>
    import.meta.env.PROD && typeof navigator !== 'undefined' && 'serviceWorker' in navigator ? 'pending' : 'none',
  );
  const [pendingDecision, setPendingDecision] = useState<Decision | null>(null);
  const [referralBody, setReferralBody] = useState<string | null>(null);
  const retakeInput = useRef<HTMLInputElement>(null);
  // 8x8 thumbnail hashes of photos already in the check, so the same photo cannot count twice.
  const seenHashes = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;
    registerOffline().then((s) => setOffline(s.ready ? 'ready' : 'none'));
  }, []);

  const go = useCallback(
    (next: ScreenId, opts: { replace?: boolean } = {}) => {
      stopVoice();
      if (!opts.replace) setTrail((tr) => [...tr, screen]);
      setScreen(next);
      window.scrollTo(0, 0);
    },
    [screen],
  );

  const back = useCallback(() => {
    stopVoice();
    setTrail((tr) => {
      const prev = tr[tr.length - 1];
      if (prev) setScreen(prev);
      return tr.slice(0, -1);
    });
  }, []);

  const resetCheck = useCallback(() => {
    chk.reset();
    for (const p of accepted) URL.revokeObjectURL(p.url);
    setAccepted([]);
    seenHashes.current = new Set();
    setRejected([]);
    setCurrent(null);
    setCredits(null);
    setReferralBody(null);
  }, [chk, accepted]);

  // New check from history or the done screen: first say which coffee block the leaves are from.
  const newCheck = useCallback(() => {
    resetCheck();
    stopVoice();
    setFarmMode('pick');
    setFarmNext('capture');
    setTrail([]);
    setScreen('farm');
    window.scrollTo(0, 0);
  }, [resetCheck]);

  const openFarm = useCallback(() => {
    setFarmMode('overview');
    go('farm');
  }, [go]);

  // Classifies photos one by one. Accepted leaves go into the check; failed ones get a retake card.
  const processPhotos = useCallback(
    async (photos: Photo[], single: boolean) => {
      let room = MAX_LEAVES - accepted.length;
      const newAccepted: Photo[] = [];
      const newRejected: Rejected[] = [];
      for (let i = 0; i < photos.length; i++) {
        const p = photos[i];
        setBusy(`${i + 1} / ${photos.length}`);
        const hash = photoHash(p.bitmap);
        if (hash !== null && seenHashes.current.has(hash)) continue; // same photo again: not counted twice
        let result: LeafResult | null = null;
        try {
          result = await classifyPhoto(p);
        } catch {
          result = null;
        }
        if (result) {
          const w = window as unknown as { __janiResults?: unknown[] };
          (w.__janiResults ??= []).push({ name: p.name, label: result.label, confidence: result.confidence, quality: result.quality, modelVersion: result.modelVersion });
        }
        const retake = result ? retakeId(result) : 'retake_blurry';
        if (result && !retake && room > 0) {
          chk.accept(result);
          newAccepted.push(p);
          if (hash !== null) seenHashes.current.add(hash);
          room -= 1;
        } else if (retake) {
          newRejected.push({ photo: p, retake, result });
        }
      }
      setBusy(null);
      setAccepted((a) => [...a, ...newAccepted]);
      if (single && newRejected.length === 1) {
        setCurrent(newRejected[0]);
        go('retake');
      } else {
        setRejected((r) => [...r, ...newRejected]);
      }
    },
    [accepted.length, chk, go],
  );

  const onFiles = useCallback(
    async (files: File[], fromCamera: boolean) => {
      setBusy('');
      const photos: Photo[] = [];
      const undecodable: Rejected[] = [];
      for (const f of files) {
        const p = await decodeFile(f, f.name);
        if (p) photos.push(p);
        else undecodable.push({ photo: { url: '', bitmap: null as unknown as ImageBitmap, sample: false, name: f.name }, retake: 'retake_blurry', result: null });
      }
      if (replacing !== null) {
        setRejected((r) => r.filter((_, i) => i !== replacing));
        setReplacing(null);
      }
      if (undecodable.length) setRejected((r) => [...r, ...undecodable]);
      await processPhotos(photos, fromCamera && files.length === 1);
    },
    [processPhotos, replacing],
  );

  const onSample = useCallback(async () => {
    setBusy('');
    try {
      const m = await loadSampleManifest();
      const photos = await loadSamplePhotos(m);
      setCredits(m.items.slice(0, photos.length));
      await processPhotos(photos, false);
    } catch {
      setBusy(null);
    }
  }, [processPhotos]);

  // See result. Photos still waiting for a retake are not dropped silently: they go into the check
  // as they are (not sure or not a leaf), so they count only in the "not sure" tile and the rule
  // table answers (too many unsure or not a leaf: ask the officer or take the photos again).
  const seeResult = useCallback(() => {
    let room = MAX_LEAVES - accepted.length;
    for (const r of rejected) {
      if (room <= 0) break;
      if (r.result) {
        chk.accept(r.result);
        room -= 1;
      }
    }
    setRejected([]);
    go('summary');
  }, [accepted.length, rejected, chk, go]);

  // Save after the decision state has landed in the hook, so the stored Check carries it.
  useEffect(() => {
    if (!pendingDecision || chk.decision !== pendingDecision) return;
    const d = pendingDecision;
    setPendingDecision(null);
    (async () => {
      let body: string | null = null;
      try {
        const saved = await chk.save();
        try {
          for (let i = 0; i < accepted.length; i++) {
            if (accepted[i].bitmap) await savePhoto(saved.id, i, await compressPhoto(accepted[i].bitmap));
          }
        } catch {
          // photos are optional; the check itself is saved
        }
      } catch {
        // storage unavailable (private window): still show the result and the referral
      }
      try {
        body = chk.referralText();
      } catch {
        body = null;
      }
      setReferralBody(body);
      const abstained = chk.card?.severity === 'ask';
      go(d === 'ask' || abstained ? 'referral' : 'done');
    })();
  }, [pendingDecision, chk, accepted, go]);

  // The referral text must be rebuilt after save() set lastCheck.
  useEffect(() => {
    if (screen === 'referral' && chk.lastCheck) {
      try {
        setReferralBody(chk.referralText());
      } catch {
        // keep previous
      }
    }
  }, [screen, chk]);

  // Start the model once offline caching has settled, or as soon as photos are taken.
  const probe =
    offline !== 'pending' || !['language', 'consent', 'stopped', 'pick', 'photo'].includes(screen) ? (
      <EngineProbe onState={setEngine} />
    ) : null;

  const header = (
    <>
      {probe}
      <TopBar
      mock={engine.ready && engine.mock}
      offline={offline}
      onBack={trail.length && screen !== 'language' ? back : undefined}
      onHistory={screen !== 'history' && screen !== 'language' ? () => go('history') : undefined}
      backLabel={t('back', lang)}
      historyLabel={t('history', lang)}
      mockLabel={import.meta.env.VITE_USE_MOCK_MODEL === 'true' ? t('mock', 'en') : t('model_missing', 'en')}
        offlineLabel={offline === 'ready' ? t('offline_ready', 'en') : t('offline_not_ready', 'en')}
      />
    </>
  );

  switch (screen) {
    case 'language':
      return (
        <LanguagePage
          header={header}
          onPick={(l) => {
            setLang(l);
            storeLang(l);
            go(consent?.main ? 'pick' : 'consent');
          }}
        />
      );
    case 'consent':
      return (
        <ConsentPage
          lang={lang}
          header={header}
          onYes={() => {
            void setConsent({ main: true, photos: false }).catch(() => undefined);
            go('pick');
          }}
          onNo={() => {
            void setConsent({ main: false, photos: false }).catch(() => undefined);
            go('stopped');
          }}
        />
      );
    case 'stopped':
      return <StoppedPage lang={lang} header={header} onBack={() => go('language')} />;
    case 'pick':
      return (
        <GuidePage
          lang={lang}
          header={header}
          step="pick"
          onNext={() => {
            setFarmMode('pick');
            setFarmNext('photo');
            go('farm');
          }}
        />
      );
    case 'photo':
      return <GuidePage lang={lang} header={header} step="photo" onNext={() => go('capture')} />;
    case 'capture':
      return (
        <>
          <CapturePage
            lang={lang}
            header={header}
            accepted={accepted}
            rejected={rejected}
            busy={busy}
            credits={credits}
            onFiles={(f, cam) => void onFiles(f, cam)}
            onSample={() => void onSample()}
            onRetake={(i) => {
              setReplacing(i);
              retakeInput.current?.click();
            }}
              onDone={seeResult}
          />
          <input
            ref={retakeInput}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => {
              const files = Array.from(e.currentTarget.files ?? []).slice(0, 1);
              e.currentTarget.value = '';
              if (files.length) void onFiles(files, true);
              else setReplacing(null);
            }}
          />
        </>
      );
    case 'retake':
      return current ? (
        <>
          <RetakePage
            lang={lang}
            header={header}
            item={current}
            onRetake={() => retakeInput.current?.click()}
            onSkip={() => {
              setCurrent(null);
              go('capture', { replace: true });
            }}
          />
          <input
            ref={retakeInput}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => {
              const files = Array.from(e.currentTarget.files ?? []).slice(0, 1);
              e.currentTarget.value = '';
              if (!files.length) return;
              setCurrent(null);
              setScreen('capture');
              void onFiles(files, true);
            }}
          />
        </>
      ) : null;
    case 'summary':
      return <SummaryPage lang={lang} header={header} summary={chk.summary} onNext={() => go('answer')} />;
    case 'answer':
      return chk.card ? <AnswerPage lang={lang} header={header} card={chk.card} onNext={() => go('decision')} /> : null;
    case 'decision':
      return (
        <DecisionPage
          lang={lang}
          header={header}
          busy={pendingDecision !== null}
          onDecide={(d) => {
            chk.setDecision(d);
            setPendingDecision(d);
          }}
        />
      );
    case 'referral':
      return <ReferralPage lang={lang} header={header} decision={chk.decision ?? 'ask'} body={referralBody} onDone={() => go('history')} />;
    case 'done':
      return (
        <DonePage
          lang={lang}
          header={header}
          decision={chk.decision ?? 'wait'}
          canRefer
          onRefer={() => go('referral')}
          onHistory={() => go('history')}
          onFarm={openFarm}
          onNew={newCheck}
        />
      );
    case 'history':
      return <HistoryPage lang={lang} header={header} onNew={newCheck} onFarm={openFarm} />;
    case 'farm':
      return (
        <FarmPage
          key={farmMode}
          lang={lang}
          header={header}
          mode={farmMode}
          onCheck={(id) => {
            if (farmMode === 'overview') {
              resetCheck();
              setBlock(id);
              setTrail([]);
              setScreen('capture');
              window.scrollTo(0, 0);
              return;
            }
            setBlock(id);
            go(farmNext);
          }}
        />
      );
  }
}
