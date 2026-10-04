import { useRef } from 'react';
import type { Lang, LeafResult } from '../engine';
import { getAnswer } from '../engine';
import { Icon } from '../components/Icon';
import { BigButton, CardBlock, Screen, SpeakerButton } from '../components/Parts';
import { cardText, t } from '../ui/strings';
import type { Photo, RetakeId, SampleItem } from '../ui/photos';

export const MAX_LEAVES = 10;

export interface Rejected {
  photo: Photo;
  retake: RetakeId;
  /** Engine result for the photo (null when it could not be decoded). */
  result: LeafResult | null;
}

/** Step 3c: photograph up to 10 leaves. Camera, file upload, or the bundled sample plot. */
export function CapturePage({
  lang,
  header,
  accepted,
  rejected,
  busy,
  credits,
  onFiles,
  onSample,
  onRetake,
  onDone,
}: {
  lang: Lang;
  header: React.ReactNode;
  accepted: Photo[];
  rejected: Rejected[];
  busy: string | null;
  credits: SampleItem[] | null;
  onFiles: (files: File[], fromCamera: boolean) => void;
  onSample: () => void;
  onRetake: (index: number) => void;
  onDone: () => void;
}) {
  const camera = useRef<HTMLInputElement>(null);
  const upload = useRef<HTMLInputElement>(null);
  const n = accepted.length;
  const full = n >= MAX_LEAVES;
  // See result needs 10 leaves in the check: accepted ones plus photos still waiting for a retake
  // (those go in as they are). Fewer leaves would give the engine's too_few_leaves card anyway.
  const pendingWithResult = rejected.filter((r) => r.result).length;
  const pick = (input: HTMLInputElement | null, fromCamera: boolean) => {
    if (!input?.files) return;
    const files = Array.from(input.files).slice(0, MAX_LEAVES - n);
    input.value = '';
    if (files.length) onFiles(files, fromCamera);
  };
  return (
    <Screen
      testId="screen-capture"
      header={header}
      footer={
        <>
          {!full ? (
            <BigButton icon="camera" label={t('take_photo', lang)} onClick={() => camera.current?.click()} disabled={!!busy} testId="take-photo" />
          ) : null}
          <BigButton
            icon="next"
            label={t('done', lang)}
            kind={full ? 'primary' : 'secondary'}
            onClick={onDone}
            disabled={n + pendingWithResult < MAX_LEAVES || !!busy}
            testId="see-result"
          />
        </>
      }
    >
      <div className="count-line" data-testid="leaf-count" data-count={n}>
        <Icon name="leaf" size={34} />
        <strong>
          {n} / {MAX_LEAVES}
        </strong>
        <span>{t('leaves', lang)}</span>
      </div>
      {n === 0 && rejected.length === 0 ? <CardBlock card={getAnswer('how_to_photograph')} lang={lang} tone="info" /> : null}

      {busy ? (
        <p className="busy" role="status" data-testid="busy">
          <span className="spinner" aria-hidden="true" /> {t('checking', lang)} {busy}
        </p>
      ) : null}

      {accepted.length ? (
        <ul className="thumbs" aria-label={t('photos_ok', lang)}>
          {accepted.map((p, i) => (
            <li key={p.url + i} className="thumb thumb-ok">
              <img src={p.url} alt="" />
              <span className="thumb-mark">
                <Icon name="check" size={18} />
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      {rejected.length ? (
        <ul className="retake-list" data-testid="retake-list">
          {groupByRetake(rejected).map(([id, items]) => {
            const c = cardText(getAnswer(id), lang);
            return (
              <li key={id} className="retake-group">
                <div className="retake-head">
                  <span className="retake-count">{items.length}</span>
                  <p lang={c.shown}>{c.text}</p>
                  <SpeakerButton id={id} lang={lang} text={c.text} textLang={c.shown} label="Play" small />
                </div>
                <ul className="thumbs">
                  {items.map(({ r, i }) => (
                    <li key={r.photo.url + i} className="thumb thumb-retake" data-retake={r.retake}>
                      <button type="button" aria-label={t('retake', lang)} onClick={() => onRetake(i)} disabled={!!busy || full}>
                        {r.photo.url ? <img src={r.photo.url} alt="" /> : <span className="thumb-empty" />}
                        <span className="thumb-mark thumb-mark-retake">
                          <Icon name="camera" size={16} />
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </li>
            );
          })}
        </ul>
      ) : null}

      <div className="alt-actions">
        <button type="button" className="link-btn" onClick={() => upload.current?.click()} disabled={!!busy || full} data-testid="upload">
          <Icon name="image" size={24} /> {t('upload', lang)}
        </button>
        {n === 0 && rejected.length === 0 ? (
          <button type="button" className="link-btn" onClick={onSample} disabled={!!busy} data-testid="sample-plot">
            <Icon name="sample" size={24} /> {t('sample', lang)}
          </button>
        ) : null}
      </div>

      {credits ? (
        <details className="credits">
          <summary>{t('credits', 'en')}</summary>
          <p>{t('sample_note', 'en')}</p>
          <ul>
            {credits.map((c) => (
              <li key={c.file}>{c.attribution}</li>
            ))}
          </ul>
        </details>
      ) : null}

      <input
        ref={camera}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        onChange={(e) => pick(e.currentTarget, true)}
        data-testid="camera-input"
      />
      <input ref={upload} type="file" accept="image/*" multiple hidden onChange={(e) => pick(e.currentTarget, false)} data-testid="upload-input" />
    </Screen>
  );
}

function groupByRetake(rejected: Rejected[]): [RetakeId, { r: Rejected; i: number }[]][] {
  const m = new Map<RetakeId, { r: Rejected; i: number }[]>();
  rejected.forEach((r, i) => {
    const list = m.get(r.retake) ?? [];
    list.push({ r, i });
    m.set(r.retake, list);
  });
  return Array.from(m.entries());
}

/** A single camera photo failed: show its retake card, one action (take again). */
export function RetakePage({
  lang,
  header,
  item,
  onRetake,
  onSkip,
}: {
  lang: Lang;
  header: React.ReactNode;
  item: Rejected;
  onRetake: () => void;
  onSkip: () => void;
}) {
  return (
    <Screen
      testId="screen-retake"
      header={header}
      footer={
        <>
          <BigButton icon="camera" label={t('retake', lang)} onClick={onRetake} testId="retake" />
          <button type="button" className="link-btn center" onClick={onSkip} data-testid="skip">
            {t('skip', lang)}
          </button>
        </>
      }
    >
      {item.photo.url ? <img className="retake-photo" src={item.photo.url} alt="" /> : null}
      <CardBlock card={getAnswer(item.retake)} lang={lang} icon={item.retake === 'retake_dark' ? 'sun' : item.retake === 'retake_on_page' ? 'page' : 'camera'} />
    </Screen>
  );
}
