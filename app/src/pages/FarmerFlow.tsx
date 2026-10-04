import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Speak } from '../components/Shell.tsx'
import { Mark } from '../components/Icons.tsx'
import { getAnswer, textFor } from '../engine/content.ts'
import { bitmapFromRgba, jpegFromBitmap } from '../engine/images.ts'
import {
  classifyLeaf,
  decide,
  getConsent,
  getProfile,
  makeSample,
  saveCheck,
  savePhoto,
  saveReferral,
  seasonWindow,
  setConsent,
  setMockHint,
  setProfile,
  summarisePlot,
  syncPending,
  buildReferral,
  play,
  smsLink,
  type AnswerCard,
  type Check,
  type Decision,
  type Lang,
  type LeafResult,
  type PlotSummary,
  type SampleKind,
} from '../engine/index.ts'
import { labelKey, t } from '../i18n.ts'
import { useLang } from '../lang.tsx'

type Step = 'language' | 'consent' | 'how' | 'capture' | 'review' | 'summary' | 'action' | 'decision' | 'referral' | 'done' | 'refused'

interface Shot {
  result: LeafResult
  url: string
  blob: Blob
  synthetic: boolean
}

const FILL: SampleKind[] = ['rust', 'rust', 'rust', 'rust', 'rust', 'rust', 'healthy', 'healthy', 'healthy', 'blur']

export function FarmerFlow() {
  const { lang, setLang } = useLang()
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('language')
  const [shots, setShots] = useState<Shot[]>([])
  const [pending, setPending] = useState<Shot | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [summary, setSummary] = useState<PlotSummary | null>(null)
  const [card, setCard] = useState<AnswerCard | null>(null)
  const [choice, setChoice] = useState<Decision | null>(null)
  const [saved, setSaved] = useState<Check | null>(null)
  const [memberId, setMemberId] = useState('')
  const [plotId, setPlotId] = useState('')
  const [coopNumber, setCoopNumber] = useState('')
  const [sharePhotos, setSharePhotos] = useState(false)
  const [consented, setConsented] = useState(false)

  useEffect(() => {
    void getConsent().then((value) => setConsented(value.main))
    void getProfile().then((value) => {
      setMemberId(value.memberId)
      setPlotId(value.plotId)
      setCoopNumber(value.coopNumber)
    })
  }, [])

  function reset() {
    setShots([])
    setPending(null)
    setSummary(null)
    setCard(null)
    setChoice(null)
    setSaved(null)
    setError('')
    setStep('how')
  }

  async function makeShot(bitmap: ImageBitmap, synthetic: boolean): Promise<Shot> {
    try {
      const result = await classifyLeaf(bitmap)
      const jpeg = await jpegFromBitmap(bitmap)
      return { result, url: jpeg.url, blob: jpeg.blob, synthetic }
    } finally {
      bitmap.close()
    }
  }

  async function onFile(file: File) {
    setError('')
    setBusy(true)
    try {
      setMockHint(file.name)
      const bitmap = await createImageBitmap(file)
      setPending(await makeShot(bitmap, false))
      setStep('review')
    } catch {
      setError(t(lang, 'photo_error'))
    } finally {
      setBusy(false)
    }
  }

  async function onSample(kind: SampleKind) {
    setError('')
    setBusy(true)
    try {
      const sample = makeSample(kind)
      setMockHint(kind)
      const bitmap = await bitmapFromRgba(sample.width, sample.height, sample.rgba)
      setPending(await makeShot(bitmap, true))
      setStep('review')
    } catch {
      setError(t(lang, 'photo_error'))
    } finally {
      setBusy(false)
    }
  }

  async function onFill() {
    setBusy(true)
    setError('')
    try {
      const next: Shot[] = []
      for (const kind of FILL) {
        const sample = makeSample(kind)
        setMockHint(kind)
        const bitmap = await bitmapFromRgba(sample.width, sample.height, sample.rgba)
        next.push(await makeShot(bitmap, true))
      }
      openSummary(next)
    } catch {
      setError(t(lang, 'photo_error'))
    } finally {
      setBusy(false)
    }
  }

  function keep() {
    if (!pending || !pending.result.quality.ok) return
    const next = [...shots, pending]
    setPending(null)
    if (next.length >= 10) openSummary(next)
    else {
      setShots(next)
      setStep('capture')
    }
  }

  function openSummary(next: Shot[]) {
    const plot = summarisePlot(next.map((shot) => shot.result))
    const answer = decide(plot, new Date())
    setShots(next)
    setSummary(plot)
    setCard(answer)
    setStep('summary')
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!reduce) void play(answer.id, lang)
  }

  async function choose(decision: Decision) {
    if (!summary || !card) return
    setChoice(decision)
    const check: Check = {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      lang,
      leaves: shots.map((shot) => shot.result),
      summary,
      window: seasonWindow(new Date()),
      answerId: card.id,
      decision,
      memberId,
      plotId,
      consentMain: true,
      consentPhotos: sharePhotos,
      synced: false,
      synthetic: shots.length > 0 && shots.every((shot) => shot.synthetic),
    }
    await saveCheck(check)
    if (sharePhotos) {
      for (let index = 0; index < shots.length; index++) {
        const shot = shots[index]
        if (shot) await savePhoto(check.id, index, shot.blob)
      }
    }
    await setProfile({ memberId, plotId, coopNumber })
    setSaved(check)
  }

  async function sendReferral() {
    if (!saved) return
    const sms = buildReferral({ ...saved, memberId, plotId, decision: saved.decision })
    if (sharePhotos) {
      for (let index = 0; index < shots.length; index++) {
        const shot = shots[index]
        if (shot) await savePhoto(saved.id, index, shot.blob)
      }
      await saveCheck({ ...saved, memberId, plotId, consentPhotos: true })
    }
    await saveReferral({
      id: saved.id,
      createdAt: saved.createdAt,
      memberId: memberId || 'NA',
      plotId: plotId || 'NA',
      checkDate: sms.split('D:')[1]?.slice(0, 8) ?? '',
      counts: {
        rust: saved.summary.counts.rust,
        cercospora: saved.summary.counts.cercospora,
        phoma: saved.summary.counts.phoma,
        miner: saved.summary.counts.miner,
        healthy: saved.summary.counts.healthy,
        not_leaf: saved.summary.counts.not_leaf,
      },
      uncertain: saved.summary.uncertain,
      answerId: saved.answerId,
      confidence: Math.round(
        (saved.leaves.filter((leaf) => !leaf.abstained).reduce((sum, leaf) => sum + leaf.confidence, 0) /
          Math.max(1, saved.leaves.filter((leaf) => !leaf.abstained).length)) *
          100,
      ),
      photosShared: sharePhotos,
      status: 'new',
      synthetic: saved.synthetic,
      sms,
      decision: saved.decision ?? 'ask',
    })
    await setProfile({ memberId, plotId, coopNumber })
    void syncPending()
  }

  const referralBody = saved ? buildReferral({ ...saved, memberId, plotId }) : ''
  const smsHref = coopNumber.trim() ? smsLink(coopNumber.trim(), referralBody) : ''
  const toolAsks = card?.severity === 'ask' || choice === 'ask'

  return (
    <section className="flow">
      {step === 'language' && (
        <>
          <h1>{t(lang, 'choose_language')}</h1>
          <p className="note">{t(lang, 'sw_review')}</p>
          <p className="note">{t(lang, 'kik_review')}</p>
          <p className="note">{t(lang, 'mock_note')}</p>
          {(['sw', 'kik', 'en'] as Lang[]).map((code) => (
            <button
              key={code}
              type="button"
              className="primary"
              onClick={() => {
                setLang(code)
                setStep(consented ? 'how' : 'consent')
              }}
            >
              <Mark kind="speaker" />
              <span>{t(code, code === 'sw' ? 'lang_sw' : code === 'kik' ? 'lang_kik' : 'lang_en')}</span>
            </button>
          ))}
        </>
      )}

      {step === 'consent' && (
        <>
          <h1>{t(lang, 'consent_title')}</h1>
          <p className="lead">{textFor(must('consent_main'), lang)}</p>
          <Speak answerId="consent_main" />
          <button
            type="button"
            className="primary"
            onClick={() => {
              void setConsent({ main: true, photos: false }).then(() => {
                setConsented(true)
                setStep('how')
              })
            }}
          >
            {t(lang, 'yes')}
          </button>
          <button type="button" className="secondary" onClick={() => setStep('refused')}>
            {t(lang, 'no')}
          </button>
        </>
      )}

      {step === 'refused' && (
        <>
          <h1>{t(lang, 'consent_stopped')}</h1>
          <button type="button" className="secondary" onClick={() => setStep('language')}>
            {t(lang, 'back')}
          </button>
        </>
      )}

      {step === 'how' && (
        <>
          <h1>{t(lang, 'how_title')}</h1>
          <p className="lead">{textFor(must('how_to_pick_leaves'), lang)}</p>
          <Speak answerId="how_to_pick_leaves" />
          <p className="lead">{textFor(must('how_to_photograph'), lang)}</p>
          <Speak answerId="how_to_photograph" />
          <p className="note">{textFor(must('other_crop'), lang)}</p>
          <button type="button" className="primary" onClick={() => setStep('capture')}>
            {t(lang, 'start_check')}
          </button>
        </>
      )}

      {step === 'capture' && (
        <>
          <h1>{t(lang, 'leaf_progress', { n: shots.length + 1 })}</h1>
          <label className="primary file">
            {t(lang, 'take_photo')}
            <input
              type="file"
              accept="image/*"
              capture="environment"
              disabled={busy}
              onChange={(event) => {
                const file = event.target.files?.[0]
                event.target.value = ''
                if (file) void onFile(file)
              }}
            />
          </label>
          <p className="note">{t(lang, 'sample_note')}</p>
          <div className="stack">
            {(['rust', 'healthy', 'blur', 'dark', 'not_leaf'] as SampleKind[]).map((kind) => (
              <button key={kind} type="button" className="secondary" disabled={busy} onClick={() => void onSample(kind)}>
                {t(lang, `sample_${kind === 'not_leaf' ? 'other' : kind}`)}
              </button>
            ))}
          </div>
          {shots.length === 0 && (
            <>
              <button type="button" className="secondary" disabled={busy} onClick={() => void onFill()}>
                {t(lang, 'fill_plot')}
              </button>
              <p className="note">{t(lang, 'fill_note')}</p>
            </>
          )}
          {shots.length > 0 && (
            <button type="button" className="primary" onClick={() => openSummary(shots)}>
              {t(lang, 'finish_early')}
            </button>
          )}
          {error && <p className="note warn">{error}</p>}
        </>
      )}

      {step === 'review' && pending && (
        <>
          <h1>{t(lang, 'review_title')}</h1>
          <img className="thumb" src={pending.url} alt="" />
          {pending.synthetic && <p className="pill mock">{t(lang, 'synthetic')}</p>}
          <p className="row">
            <Mark kind={pending.result.quality.ok ? pending.result.label : 'unsure'} />
            <span>
              {pending.result.quality.ok
                ? t(lang, labelKey(pending.result.label))
                : pending.result.quality.reason === 'dark'
                  ? textFor(must('retake_dark'), lang)
                  : pending.result.quality.reason === 'too_small'
                    ? t(lang, 'too_small')
                    : textFor(must('retake_blurry'), lang)}
            </span>
          </p>
          {pending.result.quality.ok && pending.result.label === 'not_leaf' && (
            <p className="lead">{textFor(must('not_a_leaf'), lang)}</p>
          )}
          {pending.result.quality.ok && <p className="note">{t(lang, 'quality_ok')}</p>}
          <button type="button" className="secondary" onClick={() => { setPending(null); setStep('capture') }}>
            {t(lang, 'retake')}
          </button>
          {pending.result.quality.ok && (
            <button type="button" className="primary" onClick={keep}>
              {t(lang, 'keep')}
            </button>
          )}
        </>
      )}

      {step === 'summary' && summary && card && (
        <>
          <h1>{t(lang, 'summary_title')}</h1>
          {shots.length < 10 && <p className="note">{t(lang, 'fewer_note', { n: shots.length })}</p>}
          <div className="grid">
            {shots.map((shot, index) => (
              <figure key={shot.url + index}>
                <img src={shot.url} alt="" />
                <Mark kind={shot.result.abstained ? 'unsure' : shot.result.label} />
              </figure>
            ))}
          </div>
          <p className="lead">{summaryLine(lang, summary)}</p>
          <Speak answerId={card.id} />
          <button type="button" className="primary" onClick={() => setStep('action')}>
            {t(lang, 'next')}
          </button>
        </>
      )}

      {step === 'action' && card && (
        <>
          <h1>{t(lang, 'action_title')}</h1>
          <p className={`card severity-${card.severity}`}>
            <Mark kind={card.severity === 'ask' ? 'unsure' : card.severity === 'ok' ? 'healthy' : 'leaf'} />
            <span>{textFor(card, lang)}</span>
          </p>
          {card.notSure && (
            <>
              <h2>{t(lang, 'not_sure_label')}</h2>
              <p className="lead">{textFor({ text: card.notSure }, lang)}</p>
            </>
          )}
          {card.assumption && <p className="pill mock">{t(lang, 'assumption')}</p>}
          {card.sources.length > 0 && <p className="note">{card.sources.join(', ')}</p>}
          <Speak answerId={card.id} />
          <button type="button" className="primary" onClick={() => setStep('decision')}>
            {t(lang, 'you_choose')}
          </button>
        </>
      )}

      {step === 'decision' && card && (
        <>
          <h1>{t(lang, 'decision_title')}</h1>
          <p className="note">{t(lang, 'you_choose')}</p>
          {!choice && (
            <>
              <button type="button" className="primary" onClick={() => void choose('act')}>
                {t(lang, 'act')}
              </button>
              <button type="button" className="secondary" onClick={() => void choose('wait')}>
                {t(lang, 'wait')}
              </button>
              <button type="button" className="danger" onClick={() => void choose('ask')}>
                {t(lang, 'ask')}
              </button>
            </>
          )}
          {choice && (
            <>
              <p className="lead">{textFor(must(`decision_${choice}`), lang)}</p>
              <Speak answerId={`decision_${choice}`} />
              <button
                type="button"
                className="primary"
                onClick={() => setStep(toolAsks ? 'referral' : 'done')}
              >
                {t(lang, 'next')}
              </button>
              {!toolAsks && (
                <button type="button" className="secondary" onClick={() => setStep('referral')}>
                  {t(lang, 'ask')}
                </button>
              )}
            </>
          )}
        </>
      )}

      {step === 'referral' && saved && (
        <>
          <h1>{t(lang, 'referral_title')}</h1>
          <p className="lead">{textFor(must('referral_ready'), lang)}</p>
          <Speak answerId="referral_ready" />
          <label>
            {t(lang, 'member')}
            <input value={memberId} onChange={(event) => setMemberId(event.target.value)} autoComplete="off" />
          </label>
          <label>
            {t(lang, 'plot')}
            <input value={plotId} onChange={(event) => setPlotId(event.target.value)} autoComplete="off" />
          </label>
          <label>
            {t(lang, 'coop_number')}
            <input value={coopNumber} onChange={(event) => setCoopNumber(event.target.value)} inputMode="tel" autoComplete="off" />
          </label>
          <p className="sms">{buildReferral({ ...saved, memberId, plotId })}</p>
          <p className="lead">{textFor(must('consent_photos'), lang)}</p>
          <label className="check">
            <input
              type="checkbox"
              checked={sharePhotos}
              onChange={(event) => {
                setSharePhotos(event.target.checked)
                void setConsent({ main: true, photos: event.target.checked })
              }}
            />
            <span>{t(lang, 'share_photos')}</span>
          </label>
          <p className="note">{t(lang, 'photos_kept')}</p>
          {!smsHref && <p className="note warn">{t(lang, 'need_number')}</p>}
          {smsHref ? (
            <a className="primary" href={smsHref} onClick={() => void sendReferral()}>
              {t(lang, 'send_sms')}
            </a>
          ) : (
            <button type="button" className="primary" disabled>
              {t(lang, 'send_sms')}
            </button>
          )}
          <p className="note">{t(lang, 'send_note')}</p>
          <button type="button" className="secondary" onClick={() => { void sendReferral(); setStep('done') }}>
            {t(lang, 'done')}
          </button>
          <p className="note">{t(lang, 'gateway_note')}</p>
        </>
      )}

      {step === 'done' && (
        <>
          <h1>{t(lang, 'saved')}</h1>
          {choice && <p className="lead">{textFor(must(`decision_${choice}`), lang)}</p>}
          <button type="button" className="primary" onClick={reset}>
            {t(lang, 'again')}
          </button>
          <button type="button" className="secondary" onClick={() => navigate('/officer')}>
            {t(lang, 'nav_officer')}
          </button>
        </>
      )}
    </section>
  )
}

function must(id: string) {
  const record = getAnswer(id)
  if (!record) throw new Error(`Missing answer ${id}`)
  return record
}

function summaryLine(lang: Lang, summary: PlotSummary): string {
  if (summary.dominant === 'healthy') {
    return t(lang, 'summary_healthy', { n: summary.n - summary.uncertain, uncertain: summary.uncertain })
  }
  if (summary.dominant === 'none') {
    return t(lang, 'summary_none', { uncertain: summary.uncertain })
  }
  return t(lang, 'summary_line', {
    affected: summary.affected,
    n: summary.n,
    problem: t(lang, labelKey(summary.dominant)),
    uncertain: summary.uncertain,
  })
}
