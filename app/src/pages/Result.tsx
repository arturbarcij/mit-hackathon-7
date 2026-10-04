import type { AnswerCard, Decision, Lang, PlotSummary } from '../engine';
import { getAnswer } from '../engine';
import { Icon, type IconName } from '../components/Icon';
import { BigButton, CardBlock, Screen, SpeakerButton } from '../components/Parts';
import { GROUP_ICON, GROUPS, groupCounts, groupLabel, summarySentence } from '../ui/farmer';
import { t } from '../ui/strings';

const SEVERITY_ICON: Record<AnswerCard['severity'], IconName> = { ok: 'leaf', watch: 'clock', act: 'check', ask: 'person' };

/** Tiles for the four farmer groups. Not-sure leaves are counted on their own. */
export function SummaryTiles({ summary, lang, compact }: { summary: PlotSummary; lang: Lang; compact?: boolean }) {
  const c = groupCounts(summary);
  return (
    <ul className={`tiles${compact ? ' tiles-compact' : ''}`} data-testid="tiles">
      {GROUPS.map((g) => (
        <li key={g} className={`tile tile-${g}`} data-group={g} data-count={c[g]}>
          <Icon name={GROUP_ICON[g]} size={compact ? 22 : 36} />
          <strong>{c[g]}</strong>
          <span>{groupLabel(g, lang)}</span>
        </li>
      ))}
    </ul>
  );
}

/** Step 5: plot summary as icons and counts, spoken aloud. */
export function SummaryPage({
  lang,
  header,
  summary,
  onNext,
}: {
  lang: Lang;
  header: React.ReactNode;
  summary: PlotSummary;
  onNext: () => void;
}) {
  const sentence = summarySentence(summary, lang);
  return (
    <Screen testId="screen-summary" header={header} footer={<BigButton icon="next" label={t('next', lang)} onClick={onNext} testId="summary-next" />}>
      <div className="count-line">
        <Icon name="leaf" size={34} />
        <strong>{summary.n}</strong>
        <span>{t('leaves', lang)}</span>
        <SpeakerButton id={null} lang={lang} text={sentence} label="Play" />
      </div>
      <SummaryTiles summary={summary} lang={lang} />
    </Screen>
  );
}

/** Step 6: the answer card from the rule table, the not-sure line, and the berries line under every result. */
export function AnswerPage({
  lang,
  header,
  card,
  onNext,
}: {
  lang: Lang;
  header: React.ReactNode;
  card: AnswerCard;
  onNext: () => void;
}) {
  return (
    <Screen testId="screen-answer" header={header} footer={<BigButton icon="next" label={t('next', lang)} onClick={onNext} testId="answer-next" />}>
      <CardBlock card={card} lang={lang} icon={SEVERITY_ICON[card.severity]} testId="answer-card" />
      <CardBlock card={getAnswer('berries_out_of_scope')} lang={lang} icon="berry" tone="info" testId="berries-card" />
      <p className="meta">
        {card.assumption ? <span className="badge badge-assumption">{t('assumption', 'en')}</span> : null}
        {card.sources.length ? (
          <span>
            {t('sources', 'en')}: {card.sources.join(', ')}
          </span>
        ) : null}
      </p>
    </Screen>
  );
}

const DECISION_ICON: Record<Decision, IconName> = { act: 'check', wait: 'clock', ask: 'person' };

/** Step 7: the farmer decides. Nothing is pre-selected. */
export function DecisionPage({
  lang,
  header,
  onDecide,
  busy,
}: {
  lang: Lang;
  header: React.ReactNode;
  onDecide: (d: Decision) => void;
  busy: boolean;
}) {
  return (
    <Screen testId="screen-decision" header={header}>
      <ul className="decision-list">
        {(['act', 'wait', 'ask'] as Decision[]).map((d) => (
          <li key={d} className="decision-row">
            <SpeakerButton id={null} lang={lang} text={t(d, lang)} label="Play" />
            <BigButton icon={DECISION_ICON[d]} label={t(d, lang)} kind={d === 'ask' ? 'primary' : 'secondary'} onClick={() => onDecide(d)} disabled={busy} testId={`decide-${d}`} />
          </li>
        ))}
      </ul>
    </Screen>
  );
}
