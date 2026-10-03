import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Link } from 'react-router-dom'
import { PlayButton } from '../components/PlayButton'
import { LeafMark } from '../components/LeafMark'
import { PickFigure } from '../components/PickFigure'
import { StatusBar } from '../components/StatusBar'
import { answerLine, ui } from '../components/optionalContent'
import {
  cardNotSure,
  cardText,
  decisionLine,
  formatWhen,
  leafCaption,
  leafKind,
  qualityLine,
  summarySentence,
} from '../components/words'
import type { AnswerCard, Check, Decision, Lang, LeafResult, PlotSummary, QualityResult } from '../engine/types'
import {
  buildReferral,
  checkQuality,
  classifyLeaf,
  decide,
  listChecks,
  play,
  saveCheck,
  seasonWindow,
  setConsent,
  smsLink,
  summarisePlot,
} from '../engine'

type Step =
  | 'language'
  | 'consent'
  | 'stopped'
  | 'howto'
  | 'capture'
  | 'summary'
  | 'action'
  | 'decision'
  | 'referral'
  | 'saved'
  | 'history'

interface PendingPhoto {
  previewUrl: string
  quality: QualityResult
  result: LeafResult
}

interface KeptLeaf {
  previewUrl: string
  result: LeafResult
}

interface FlowDraft {
  step: Step
  lang: Lang | null
  kept: KeptLeaf[]
  pending: PendingPhoto | null
  summary: PlotSummary | null
  answer: AnswerCard | null
  check: Check | null
  choice: Decision | null
  returnStep: Step
  member: string
  plot: string
  coop: string
  sharePhotos: boolean
  run: number
}

const KIKUYU_AUDIO = 'Kikuyu audio is not ready. Pending native speaker review.'

const emptyDraft = (): FlowDraft => ({
  step: 'language',
  lang: null,
  kept: [],
  pending: null,
  summary: null,
  answer: null,
  check: null,
  choice: null,
  returnStep: 'language',
  member: '',
  plot: '',
  coop: '',
  sharePhotos: false,
  run: 0,
})

let flowDraft: FlowDraft = emptyDraft()
let lastAutoplayKey = ''

function newId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `check-${Date.now()}`
}

function revokePending(photo: PendingPhoto | null) {
  if (photo) URL.revokeObjectURL(photo.previewUrl)
}

function photoProblem(reason: QualityResult['reason'], lang: Lang): string {
  if (reason === 'blurry') return answerLine('retake_blurry', lang) ?? qualityLine(reason)
  if (reason === 'dark') return answerLine('retake_dark', lang) ?? qualityLine(reason)
  return qualityLine(reason)
}

function leafProgress(lang: Lang, n: number): string {
  return ui(lang, 'leaf_of', 'Leaf {n} of {total}')
    .replaceAll('{n}', String(n))
    .replaceAll('{total}', '10')
}

export default function FarmerPage() {
  const [step, setStep] = useState<Step>(flowDraft.step)
  const [lang, setLang] = useState<Lang | null>(flowDraft.lang)
  const [kept, setKept] = useState<KeptLeaf[]>(flowDraft.kept)
  const [pending, setPending] = useState<PendingPhoto | null>(flowDraft.pending)
  const [summary, setSummary] = useState<PlotSummary | null>(flowDraft.summary)
  const [answer, setAnswer] = useState<AnswerCard | null>(flowDraft.answer)
  const [check, setCheck] = useState<Check | null>(flowDraft.check)
  const [choice, setChoice] = useState<Decision | null>(flowDraft.choice)
  const [returnStep, setReturnStep] = useState<Step>(flowDraft.returnStep)
  const [member, setMember] = useState(flowDraft.member)
  const [plot, setPlot] = useState(flowDraft.plot)
  const [coop, setCoop] = useState(flowDraft.coop)
  const [sharePhotos, setSharePhotos] = useState(flowDraft.sharePhotos)
  const [run, setRun] = useState(flowDraft.run)
  const [history, setHistory] = useState<Check[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const photoToken = useRef(0)

  useEffect(() => {
    flowDraft = {
      step,
      lang,
      kept,
      pending,
      summary,
      answer,
      check,
      choice,
      returnStep,
      member,
      plot,
      coop,
      sharePhotos,
      run,
    }
  })

  useEffect(() => {
    if (step !== 'summary' || !answer || !lang) return
    const key = `${run}:${answer.id}:${lang}`
    if (lastAutoplayKey === key) return
    lastAutoplayKey = key
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    try {
      void Promise.resolve(play(answer.id, lang)).catch(() => undefined)
    } catch {
      /* Replay stays available if autoplay cannot start. */
    }
  }, [step, answer, lang, run])

  useEffect(() => {
    if (step !== 'history') return
    let active = true
    void Promise.resolve()
      .then(() => listChecks())
      .then((rows) => {
        if (active) setHistory(rows)
      })
      .catch(() => {
        if (!active) return
        setHistory([])
        setError('Checks could not be read.')
      })
    return () => {
      active = false
    }
  }, [step])

  useEffect(() => {
    if (step !== 'referral' || !check) return
    const next: Check = {
      ...check,
      memberId: member.trim(),
      plotId: plot.trim(),
      consentPhotos: sharePhotos,
    }
    const timer = window.setTimeout(() => {
      void Promise.resolve()
        .then(() => saveCheck(next))
        .catch(() => undefined)
    }, 300)
    return () => window.clearTimeout(timer)
  }, [step, check, member, plot, sharePhotos])

  function go(next: Step) {
    setError('')
    setStep(next)
  }

  function chooseLanguage(next: Lang) {
    setLang(next)
    go('consent')
  }

  async function agree() {
    setBusy(true)
    setError('')
    try {
      await setConsent({ main: true, photos: false })
      go('howto')
    } catch {
      setError('Consent could not be saved on this phone.')
    } finally {
      setBusy(false)
    }
  }

  function openSummary(leaves: KeptLeaf[]) {
    try {
      const plotSummary = summarisePlot(leaves.map((leaf) => leaf.result))
      const card = decide(plotSummary, new Date())
      setSummary(plotSummary)
      setAnswer(card)
      go('summary')
    } catch {
      setError('The check could not be read. Ask the officer.')
    }
  }

  async function onPhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const token = photoToken.current + 1
    photoToken.current = token
    setBusy(true)
    setError('')
    try {
      const bitmap = await createImageBitmap(file)
      try {
        const quality = checkQuality(bitmap)
        const result = await classifyLeaf(bitmap, { hint: file.name })
        if (token !== photoToken.current) return
        const previewUrl = URL.createObjectURL(file)
        setPending((current) => {
          revokePending(current)
          return { previewUrl, quality, result }
        })
      } finally {
        bitmap.close()
      }
    } catch {
      if (token === photoToken.current) setError('This photo could not be read. Try another.')
    } finally {
      if (token === photoToken.current) setBusy(false)
    }
  }

  function keepLeaf() {
    if (!pending || !pending.quality.ok) return
    const next = [...kept, { previewUrl: pending.previewUrl, result: pending.result }]
    setPending(null)
    setKept(next)
    if (next.length >= 10) openSummary(next)
  }

  function retake() {
    revokePending(pending)
    setPending(null)
  }

  function finishEarly() {
    if (kept.length < 1) return
    revokePending(pending)
    setPending(null)
    openSummary(kept)
  }

  async function onDecide(nextChoice: Decision) {
    if (!lang || !summary || !answer) return
    setBusy(true)
    setError('')
    try {
      const next: Check = {
        id: newId(),
        createdAt: new Date().toISOString(),
        lang,
        leaves: kept.map((leaf) => leaf.result),
        summary,
        window: seasonWindow(new Date()),
        answerId: answer.id,
        decision: nextChoice,
        consentMain: true,
        consentPhotos: false,
        synced: false,
      }
      await saveCheck(next)
      setCheck(next)
      setChoice(nextChoice)
      if (nextChoice === 'ask' || answer.severity === 'ask') go('referral')
      else go('saved')
    } catch {
      setError('The check could not be saved on this phone.')
    } finally {
      setBusy(false)
    }
  }

  function startAnother() {
    for (const leaf of kept) URL.revokeObjectURL(leaf.previewUrl)
    revokePending(pending)
    setKept([])
    setPending(null)
    setSummary(null)
    setAnswer(null)
    setCheck(null)
    setChoice(null)
    setMember('')
    setPlot('')
    setCoop('')
    setSharePhotos(false)
    setRun((value) => value + 1)
    go(lang ? 'howto' : 'language')
  }

  function openHistory() {
    setReturnStep(step === 'history' ? returnStep : step)
    go('history')
  }

  const copyLang: Lang = lang ?? 'en'
  const leafNumber = Math.min(kept.length + 1, 10)
  const howTo = lang ? answerLine('how_to_pick_leaves', lang) : null

  return (
    <main className="app">
      <header className="top">
        <StatusBar lang={lang} />
        <nav className="nav" aria-label="Sections">
          {step !== 'history' ? (
            <button type="button" className="btn btn-quiet" onClick={openHistory}>
              {ui(copyLang, 'history', 'History')}
            </button>
          ) : null}
          <Link className="btn btn-quiet" to="/sources">
            {ui(copyLang, 'sources', 'Sources')}
          </Link>
          <Link className="btn btn-quiet" to="/officer">
            Officer view
          </Link>
        </nav>
        {lang === 'kik' && step !== 'language' ? <p className="warn">{KIKUYU_AUDIO}</p> : null}
      </header>

      {step === 'language' ? (
        <section className="screen">
          <h1>{ui(copyLang, 'choose_language', 'Choose a language.')}</h1>
          <div className="choice">
            <button type="button" className="btn btn-primary" onClick={() => chooseLanguage('sw')}>
              Kiswahili
            </button>
            <PlayButton answerId="language_name" lang="sw" />
          </div>
          <div className="choice">
            <button type="button" className="btn btn-primary" onClick={() => chooseLanguage('kik')}>
              Gikuyu
            </button>
            <PlayButton answerId="language_name" lang="kik" />
          </div>
          <p className="warn">{KIKUYU_AUDIO}</p>
          <div className="choice">
            <button type="button" className="btn btn-primary" onClick={() => chooseLanguage('en')}>
              English
            </button>
            <PlayButton answerId="language_name" lang="en" />
          </div>
        </section>
      ) : null}

      {step === 'consent' && lang ? (
        <section className="screen">
          <h1>{ui(lang, 'consent_title', 'Consent')}</h1>
          <p>
            {answerLine('consent_main', lang) ??
              ui(
                lang,
                'consent_body',
                'This check stays on this phone. Photos stay on this phone unless you later agree to share them. Nothing is sent now.',
              )}
          </p>
          <PlayButton answerId="consent_main" lang={lang} />
          {error ? <p role="alert">{error}</p> : null}
          <div className="actions">
            <button type="button" className="btn btn-primary" onClick={() => void agree()} disabled={busy}>
              {ui(lang, 'yes', 'Yes')}
            </button>
            <button type="button" className="btn btn-quiet" onClick={() => go('stopped')}>
              {ui(lang, 'no', 'No')}
            </button>
          </div>
        </section>
      ) : null}

      {step === 'stopped' ? (
        <section className="screen">
          <h1>{ui(copyLang, 'stopped_title', 'Stopped')}</h1>
          <p>{ui(copyLang, 'stopped_body', 'Nothing was saved.')}</p>
          <button type="button" className="btn btn-primary" onClick={() => go('consent')}>
            {ui(copyLang, 'back', 'Back')}
          </button>
        </section>
      ) : null}

      {step === 'howto' && lang ? (
        <section className="screen">
          <h1>{ui(lang, 'howto_title', 'How to pick')}</h1>
          <PickFigure />
          {howTo ? (
            <p>{howTo}</p>
          ) : (
            <>
              <p>{ui(lang, 'howto_rows', 'Pick 10 leaves from the worst rows.')}</p>
              <p>{ui(lang, 'howto_house', 'Bring them to the house.')}</p>
              <p>{ui(lang, 'howto_page', 'Lay them on a plain page.')}</p>
            </>
          )}
          <PlayButton answerId="how_to_pick_leaves" lang={lang} />
          <button type="button" className="btn btn-primary" onClick={() => go('capture')}>
            {ui(lang, 'next', 'Next')}
          </button>
        </section>
      ) : null}

      {step === 'capture' && lang ? (
        <section className="screen" aria-busy={busy}>
          <h1>{leafProgress(lang, leafNumber)}</h1>
          <p>
            {kept.length} {ui(lang, 'kept', 'kept.')}
          </p>
          {busy ? <p className="busy">{ui(lang, 'reading_photo', 'Reading the photo.')}</p> : null}
          {error ? <p role="alert">{error}</p> : null}
          {pending ? (
            <div className="shot">
              {pending.previewUrl ? <img src={pending.previewUrl} alt="" /> : null}
              {pending.quality.ok ? (
                <div className="caption">
                  <LeafMark kind={leafKind(pending.result)} />
                  <span>{leafCaption(pending.result)}</span>
                </div>
              ) : (
                <p>{photoProblem(pending.quality.reason, lang)}</p>
              )}
            </div>
          ) : null}
          <div className="actions">
            {pending && pending.quality.ok ? (
              <button type="button" className="btn btn-primary" onClick={keepLeaf}>
                {ui(lang, 'keep_leaf', 'Keep this leaf')}
              </button>
            ) : (
              <label className="btn btn-primary file-btn">
                {pending ? ui(lang, 'retake', 'Retake') : ui(lang, 'take_photo', 'Take photo')}
                <input type="file" accept="image/*" capture="environment" onChange={(event) => void onPhoto(event)} />
              </label>
            )}
            {pending && pending.quality.ok ? (
              <button type="button" className="btn btn-quiet" onClick={retake}>
                {ui(lang, 'retake', 'Retake')}
              </button>
            ) : null}
            {kept.length > 0 ? (
              <button type="button" className="btn btn-quiet" onClick={finishEarly}>
                Finish early
              </button>
            ) : null}
          </div>
        </section>
      ) : null}

      {step === 'summary' && lang && summary && answer ? (
        <section className="screen">
          <h1>{ui(lang, 'summary_title', 'Summary')}</h1>
          <p>{summarySentence(summary)}</p>
          <div className="grid">
            {kept.map((leaf, index) => (
              <div className="shot" key={`${leaf.previewUrl}-${index}`}>
                {leaf.previewUrl ? <img src={leaf.previewUrl} alt="" /> : null}
                <div className="caption">
                  <LeafMark kind={leafKind(leaf.result)} />
                  <span>{leafCaption(leaf.result)}</span>
                </div>
              </div>
            ))}
          </div>
          <PlayButton answerId={answer.id} lang={lang} label={ui(lang, 'replay', 'Replay')} />
          <button type="button" className="btn btn-primary" onClick={() => go('action')}>
            {ui(lang, 'next', 'Next')}
          </button>
        </section>
      ) : null}

      {step === 'action' && lang && answer ? (
        <section className="screen">
          <h1>{ui(lang, 'advice_title', 'Advice')}</h1>
          <p>{cardText(answer, lang)}</p>
          {cardNotSure(answer, lang) ? <p className="note">{cardNotSure(answer, lang)}</p> : null}
          {answer.assumption ? <p className="tag">assumption</p> : null}
          {answer.sources.length > 0 ? (
            <ul className="list">
              {answer.sources.map((source) => (
                <li key={source}>{source}</li>
              ))}
            </ul>
          ) : null}
          <PlayButton answerId={answer.id} lang={lang} />
          <Link className="btn btn-quiet" to="/sources">
            {ui(lang, 'sources_link', 'Sources and limits')}
          </Link>
          <button type="button" className="btn btn-primary" onClick={() => go('decision')}>
            {ui(lang, 'next', 'Next')}
          </button>
        </section>
      ) : null}

      {step === 'decision' && lang ? (
        <section className="screen">
          <h1>{ui(lang, 'decision_title', 'You choose.')}</h1>
          <p>{ui(lang, 'app_does_not_choose', 'The app does not choose.')}</p>
          {error ? <p role="alert">{error}</p> : null}
          <div className="actions">
            <button type="button" className="btn btn-primary" onClick={() => void onDecide('act')} disabled={busy}>
              {ui(lang, 'act', 'I will act')}
            </button>
            <button type="button" className="btn btn-quiet" onClick={() => void onDecide('wait')} disabled={busy}>
              {ui(lang, 'wait', 'I will wait')}
            </button>
            <button type="button" className="btn btn-ask" onClick={() => void onDecide('ask')} disabled={busy}>
              {ui(lang, 'ask', 'Ask the officer')}
            </button>
          </div>
        </section>
      ) : null}

      {step === 'referral' && lang && check ? (
        <ReferralStep
          lang={lang}
          check={check}
          member={member}
          plot={plot}
          coop={coop}
          sharePhotos={sharePhotos}
          error={error}
          onMember={setMember}
          onPlot={setPlot}
          onCoop={setCoop}
          onShare={(photos) => {
            setSharePhotos(photos)
            void Promise.resolve()
              .then(() => setConsent({ main: true, photos }))
              .catch(() => {
                setError('Consent was not saved.')
              })
          }}
        />
      ) : null}

      {step === 'saved' && lang ? (
        <section className="screen">
          <h1>{ui(lang, 'saved_title', 'Saved.')}</h1>
          <p>{decisionLine(choice ?? undefined)}</p>
          <button type="button" className="btn btn-primary" onClick={startAnother}>
            {ui(lang, 'new_check', 'New check')}
          </button>
        </section>
      ) : null}

      {step === 'history' ? (
        <section className="screen">
          <h1>{ui(copyLang, 'history', 'History')}</h1>
          {error ? <p role="alert">{error}</p> : null}
          {history.length === 0 ? <p>{ui(copyLang, 'history_empty', 'No checks yet.')}</p> : null}
          <ul className="list">
            {[...history]
              .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
              .map((item) => (
                <li key={item.id}>
                  <p>{formatWhen(item.createdAt)}</p>
                  <p>{decisionLine(item.decision)}</p>
                  <p>{item.summary ? summarySentence(item.summary) : item.answerId}</p>
                </li>
              ))}
          </ul>
          <button type="button" className="btn btn-primary" onClick={() => go(returnStep)}>
            {ui(copyLang, 'back', 'Back')}
          </button>
        </section>
      ) : null}
    </main>
  )
}

interface ReferralStepProps {
  lang: Lang
  check: Check
  member: string
  plot: string
  coop: string
  sharePhotos: boolean
  error: string
  onMember: (value: string) => void
  onPlot: (value: string) => void
  onCoop: (value: string) => void
  onShare: (photos: boolean) => void
}

function ReferralStep({
  lang,
  check,
  member,
  plot,
  coop,
  sharePhotos,
  error,
  onMember,
  onPlot,
  onCoop,
  onShare,
}: ReferralStepProps) {
  const draft: Check = {
    ...check,
    memberId: member.trim(),
    plotId: plot.trim(),
    consentPhotos: sharePhotos,
  }
  let preview = ''
  let href = ''
  try {
    preview = buildReferral(draft)
    href = smsLink(coop.trim(), preview)
  } catch {
    preview = ''
    href = ''
  }

  return (
    <section className="screen">
      <h1>{ui(lang, 'referral_title', 'Ask the officer')}</h1>
      <label className="field">
        <span>{ui(lang, 'member_number', 'Member number')}</span>
        <input
          value={member}
          onChange={(event) => onMember(event.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
      </label>
      <label className="field">
        <span>{ui(lang, 'plot', 'Plot')}</span>
        <input value={plot} onChange={(event) => onPlot(event.target.value)} autoComplete="off" spellCheck={false} />
      </label>
      <label className="field">
        <span>{ui(lang, 'cooperative_number', 'Cooperative number')}</span>
        <input
          value={coop}
          onChange={(event) => onCoop(event.target.value)}
          autoComplete="off"
          inputMode="tel"
          spellCheck={false}
        />
      </label>
      <div>
        <p>{ui(lang, 'message', 'Message')}</p>
        {preview ? (
          <p className="sms" aria-live="polite">
            {preview}
          </p>
        ) : (
          <p role="alert">{ui(lang, 'message_failed', 'The message could not be built.')}</p>
        )}
        {preview.length > 160 ? <p role="alert">This message is too long.</p> : null}
      </div>
      <label className="check">
        <input
          type="checkbox"
          checked={sharePhotos}
          onChange={(event) => onShare(event.target.checked)}
        />
        <span>Also share photos when online</span>
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <p>{ui(lang, 'you_press_send', 'This opens your message app. You press send.')}</p>
      <PlayButton answerId="referral_ready" lang={lang} />
      {preview ? (
        <a className="btn btn-primary" href={href}>
          {ui(lang, 'send_sms', 'Send SMS')}
        </a>
      ) : null}
    </section>
  )
}
