// "My farm" screen: schematic map of the 2 ha with each coffee block coloured by its last leaf check.
// Works offline: reads only checks stored on this phone. Two uses:
//  - mode 'pick': after "how to pick leaves", Noor taps the block the leaves came from.
//  - mode 'overview': where to look next, and what each block showed last time.
import { useEffect, useMemo, useState } from 'react';
import { getAnswer, listChecks, seasonWindow, type Check, type Lang } from '../engine';
import { Icon, type IconName } from '../components/Icon';
import { BigButton, CardBlock, Screen, SpeakerButton } from '../components/Parts';
import { SummaryTiles } from './Result';
import { t, windowLabel } from '../ui/strings';
import {
  blockStates,
  exampleChecks,
  FARM_BLOCKS,
  nextBlock,
  RECHECK_DAYS,
  unassignedChecks,
  type BlockState,
  type BlockStatus,
  type FarmBlock,
} from '../ui/farm';

const STATUS_ICON: Record<BlockStatus, IconName> = { act: 'rust', ask: 'person', watch: 'clock', ok: 'leaf', none: 'question' };
const LEGEND: readonly BlockStatus[] = ['act', 'ask', 'watch', 'ok', 'none'];

function statusLabel(s: BlockStatus, lang: Lang): string {
  return t(`status_${s}` as const, lang);
}

export function blockName(b: FarmBlock, lang: Lang): string {
  const crop = t(b.crop, lang);
  return b.crop === 'coffee' ? `${crop} ${b.n}` : crop;
}

function ago(n: number | null, lang: Lang): string {
  if (n === null) return '';
  if (n === 0) return t('today', lang);
  return n === 1 ? t('day_ago', lang) : `${n} ${t('days_ago', lang)}`;
}

function fmtDate(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

export function FarmPage({
  lang,
  header,
  mode,
  onCheck,
  now: nowProp,
}: {
  lang: Lang;
  header: React.ReactNode;
  mode: 'pick' | 'overview';
  onCheck: (blockId: string) => void;
  now?: Date;
}) {
  const [now] = useState(() => nowProp ?? new Date());
  const [checks, setChecks] = useState<Check[] | null>(null);
  const [example, setExample] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    listChecks().then(setChecks, () => setChecks([]));
  }, []);

  const source = useMemo(() => (example ? exampleChecks(now) : checks ?? []), [example, checks, now]);
  const states = useMemo(() => blockStates(source, now), [source, now]);
  const next = useMemo(() => nextBlock(states), [states]);
  const byId = useMemo(() => new Map(states.map((s) => [s.block.id, s])), [states]);
  const sel = selected ? byId.get(selected) ?? null : null;
  const loose = example ? 0 : unassignedChecks(checks ?? []);
  const nothingYet = checks !== null && !example && states.every((s) => s.status === 'none');
  const win = seasonWindow(now);

  const title = mode === 'pick' ? t('which_block', lang) : t('my_farm', lang);

  return (
    <Screen
      testId="screen-farm"
      header={header}
      footer={
        <BigButton
          icon={mode === 'pick' ? 'next' : 'camera'}
          label={sel ? `${t('check_block', lang)}: ${blockName(sel.block, lang)}` : t('tap_block', lang)}
          disabled={!sel}
          onClick={() => sel && onCheck(sel.block.id)}
          testId="farm-check"
        />
      }
    >
      <div className="count-line">
        <Icon name="map" size={34} />
        <h1 className="page-title farm-title">{title}</h1>
        <SpeakerButton id={null} lang={lang} text={title} label="Play" />
      </div>

      {mode === 'overview' ? (
        <p className="farm-now" data-testid="farm-window">
          <Icon name="clock" size={22} /> {t('now_window', lang)}: <strong>{windowLabel(win, lang)}</strong>
        </p>
      ) : null}

      {mode === 'overview' && next && !nothingYet ? (
        <button type="button" className={`farm-next tone-${next.status === 'none' ? 'info' : next.status}`} onClick={() => setSelected(next.block.id)} data-testid="farm-next">
          <Icon name="next" size={26} />
          <span>
            {t('check_next', lang)}: <strong>{blockName(next.block, lang)}</strong>
            <small>{next.status === 'none' ? t('status_none', lang) : next.overdue ? t('overdue', lang) : statusLabel(next.status, lang)}</small>
          </span>
        </button>
      ) : null}

      <FarmMap states={byId} selected={selected} onSelect={setSelected} lang={lang} />

      <ul className="farm-legend" aria-label="Legend">
        {LEGEND.map((s) => (
          <li key={s} className={`legend-${s}`}>
            <span className={`swatch blk-${s}`} aria-hidden="true" />
            <Icon name={STATUS_ICON[s]} size={18} />
            {statusLabel(s, lang)}
          </li>
        ))}
      </ul>

      <ul className="farm-blocks" data-testid="farm-blocks">
        {states.map((s) => (
          <li key={s.block.id}>
            <button
              type="button"
              className={`farm-block-btn tone-${s.status === 'none' ? 'info' : s.status}${selected === s.block.id ? ' is-selected' : ''}`}
              onClick={() => setSelected(s.block.id)}
              aria-pressed={selected === s.block.id}
              data-testid={`block-${s.block.id}`}
              data-status={s.status}
            >
              <Icon name={STATUS_ICON[s.status]} size={26} />
              <span className="fb-name">{blockName(s.block, lang)}</span>
              <span className="fb-meta">
                {s.last ? ago(s.daysAgo, lang) : t('status_none', lang)}
                {s.last && s.overdue ? ` · ${t('overdue', lang)}` : ''}
              </span>
            </button>
          </li>
        ))}
      </ul>

      {sel ? <BlockDetail state={sel} lang={lang} /> : null}

      {nothingYet ? (
        <p className="meta" data-testid="farm-empty">
          {t('no_checks', lang)}.{' '}
          <button type="button" className="link-btn" onClick={() => setExample(true)} data-testid="farm-example">
            {t('example', lang)}
          </button>
        </p>
      ) : null}
      {example ? (
        <p className="farm-note">
          <span className="badge badge-assumption">{t('example_note', 'en')}</span>{' '}
          <button type="button" className="link-btn" onClick={() => setExample(false)}>
            {t('hide_example', lang)}
          </button>
        </p>
      ) : null}
      {loose > 0 ? (
        <p className="meta">
          {loose} {t('unassigned', lang)}
        </p>
      ) : null}
      <p className="farm-note">{t('schematic_note', 'en')}</p>
    </Screen>
  );
}

function BlockDetail({ state, lang }: { state: BlockState; lang: Lang }) {
  const { block, last } = state;
  return (
    <section className="farm-detail" data-testid="farm-detail" aria-live="polite">
      <h2>
        <Icon name={STATUS_ICON[state.status]} size={26} /> {blockName(block, lang)}
      </h2>
      {last ? (
        <>
          <p className="meta">
            {t('last_check', lang)}: <time dateTime={last.createdAt}>{last.createdAt.slice(0, 10)}</time> ({ago(state.daysAgo, lang)})
            {last.decision ? <span className="badge">{t(last.decision, lang)}</span> : null}
          </p>
          <SummaryTiles summary={last.summary} lang={lang} compact />
          <CardBlock card={getAnswer(last.answerId)} lang={lang} showNotSure={false} />
          {state.due ? (
            <p className={`farm-due${state.overdue ? ' is-overdue' : ''}`} data-testid="farm-due">
              <Icon name="clock" size={22} /> {t('check_again_by', lang)}: <strong>{fmtDate(state.due)}</strong>{' '}
              <span className="badge badge-assumption">
                {t('assumption', 'en')}: {RECHECK_DAYS} days, officer to confirm
              </span>
            </p>
          ) : null}
        </>
      ) : (
        <p className="meta">{t('status_none', lang)}</p>
      )}
    </section>
  );
}

function FarmMap({
  states,
  selected,
  onSelect,
  lang,
}: {
  states: Map<string, BlockState>;
  selected: string | null;
  onSelect: (id: string) => void;
  lang: Lang;
}) {
  return (
    <svg className="farm-map" viewBox="0 0 340 400" role="group" aria-label={t('my_farm', lang)} data-testid="farm-map">
      <defs>
        <pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="8" height="8" className="hatch-bg" />
          <line x1="0" y1="0" x2="0" y2="8" className="hatch-line" />
        </pattern>
      </defs>
      <text x="170" y="14" className="map-slope" textAnchor="middle">
        {t('upper_slope', lang)} ↑
      </text>
      {FARM_BLOCKS.map((b) => {
        const s = states.get(b.id);
        const status: BlockStatus | 'crop' = b.checkable ? s?.status ?? 'none' : 'crop';
        const isSel = selected === b.id;
        const name = blockName(b, lang);
        const common = {
          d: b.path,
          className: `blk blk-${status}${b.checkable ? ' blk-tap' : ''}${isSel ? ' is-selected' : ''}`,
        };
        return (
          <g key={b.id} data-block={b.id} data-status={status}>
            {b.checkable ? (
              <path
                {...common}
                role="button"
                tabIndex={0}
                aria-pressed={isSel}
                aria-label={`${name}: ${statusLabel(status as BlockStatus, lang)}`}
                onClick={() => onSelect(b.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect(b.id);
                  }
                }}
              />
            ) : (
              <path {...common} aria-hidden="true" />
            )}
            <text x={b.label[0]} y={b.label[1]} className="map-label" textAnchor="middle" pointerEvents="none">
              {name}
            </text>
            {b.checkable ? (
              <text x={b.label[0]} y={b.label[1] + 20} className="map-sub" textAnchor="middle" pointerEvents="none">
                {s?.last ? `${s.last.summary.counts.rust}/${s.last.summary.n} ${t('rust', lang).toLowerCase()}` : '-'}
              </text>
            ) : (
              <text x={b.label[0]} y={b.label[1] + 18} className="map-sub" textAnchor="middle" pointerEvents="none">
                {t('coffee_only', lang)}
              </text>
            )}
          </g>
        );
      })}
      {/* The house: where the phone stays and where the leaves are photographed. */}
      <g className="map-house" transform="translate(150 334)">
        <path d="M0 18 L20 2 L40 18 L40 40 L0 40 Z" />
        <text x="20" y="54" textAnchor="middle" className="map-sub">
          {t('home', lang)}
        </text>
      </g>
    </svg>
  );
}
