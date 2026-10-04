import { useEffect, useState } from 'react';
import type { Check, Decision, Lang } from '../engine';
import { getAnswer, listChecks, smsLink } from '../engine';
import { Icon } from '../components/Icon';
import { BigButton, CardBlock, Screen } from '../components/Parts';
import { cardText, t } from '../ui/strings';
import { SummaryTiles } from './Result';

/** Cooperative SMS number. Set VITE_COOP_NUMBER at build time; the default is a demo placeholder. */
export const COOP_NUMBER: string = import.meta.env.VITE_COOP_NUMBER || '+254700000000';
export const COOP_IS_DEMO = !import.meta.env.VITE_COOP_NUMBER;

/** Step 8: referral SMS preview. The SMS app opens only when the farmer taps Send; she presses send there. */
export function ReferralPage({
  lang,
  header,
  decision,
  body,
  onDone,
}: {
  lang: Lang;
  header: React.ReactNode;
  decision: Decision;
  body: string | null;
  onDone: () => void;
}) {
  return (
    <Screen
      testId="screen-referral"
      header={header}
      footer={
        <>
          <BigButton
            icon="sms"
            label={t('send_sms', lang)}
            disabled={!body}
            onClick={() => {
              if (!body) return;
              window.location.href = smsLink(COOP_NUMBER, body);
            }}
            testId="send-sms"
          />
          <BigButton icon="history" label={t('history', lang)} kind="secondary" onClick={onDone} testId="referral-done" />
        </>
      }
    >
      <CardBlock card={getAnswer(`decision_${decision}`)} lang={lang} icon="person" tone="info" />
      <CardBlock card={getAnswer('referral_ready')} lang={lang} icon="sms" tone="info" />
      {body ? (
        <figure className="sms-preview" data-testid="sms-preview">
          <code>{body}</code>
          <figcaption>
            {body.length} / 160 {t('chars', 'en')} · {COOP_NUMBER}
            {COOP_IS_DEMO ? <span className="badge badge-assumption">{t('demo_number', 'en')}</span> : null}
          </figcaption>
        </figure>
      ) : null}
    </Screen>
  );
}

/** After act or wait: the decision card, then history or a new check. */
export function DonePage({
  lang,
  header,
  decision,
  canRefer,
  onRefer,
  onHistory,
  onFarm,
  onNew,
}: {
  lang: Lang;
  header: React.ReactNode;
  decision: Decision;
  canRefer: boolean;
  onRefer: () => void;
  onHistory: () => void;
  onFarm?: () => void;
  onNew: () => void;
}) {
  return (
    <Screen
      testId="screen-done"
      header={header}
      footer={
        <>
          <BigButton icon="plus" label={t('new_check', lang)} onClick={onNew} testId="new-check" />
          {onFarm ? <BigButton icon="map" label={t('my_farm', lang)} kind="secondary" onClick={onFarm} testId="done-farm" /> : null}
          <BigButton icon="history" label={t('history', lang)} kind="secondary" onClick={onHistory} />
        </>
      }
    >
      <CardBlock card={getAnswer(`decision_${decision}`)} lang={lang} icon={decision === 'act' ? 'check' : 'clock'} tone="info" />
      {canRefer ? (
        <button type="button" className="link-btn" onClick={onRefer} data-testid="refer-anyway">
          <Icon name="sms" size={24} /> {t('ask', lang)}
        </button>
      ) : null}
    </Screen>
  );
}

/** Local history: checks saved on this phone, newest first. */
export function HistoryPage({ lang, header, onNew, onFarm }: { lang: Lang; header: React.ReactNode; onNew: () => void; onFarm?: () => void }) {
  const [checks, setChecks] = useState<Check[] | null>(null);
  useEffect(() => {
    listChecks().then(setChecks, () => setChecks([]));
  }, []);
  return (
    <Screen
      testId="screen-history"
      header={header}
      footer={
        <>
          <BigButton icon="plus" label={t('new_check', lang)} onClick={onNew} />
          {onFarm ? <BigButton icon="map" label={t('my_farm', lang)} kind="secondary" onClick={onFarm} testId="history-farm" /> : null}
        </>
      }
    >
      <h1 className="page-title">
        <Icon name="history" size={30} /> {t('history', lang)}
      </h1>
      {checks && checks.length === 0 ? <p className="meta">{t('no_checks', lang)}</p> : null}
      <ul className="history" data-testid="history-list">
        {(checks ?? []).map((c) => {
          const card = getAnswer(c.answerId);
          const text = cardText(card, lang);
          return (
            <li key={c.id} className={`history-item tone-${card.severity}`}>
              <div className="history-head">
                <time dateTime={c.createdAt}>{c.createdAt.slice(0, 10)}</time>
                {c.plotId && c.plotId.includes('-') ? <span className="badge">{c.plotId.split('-').pop()}</span> : null}
                {c.decision ? <span className="badge">{t(c.decision, lang)}</span> : null}
              </div>
              <SummaryTiles summary={c.summary} lang={lang} compact />
              <p className="history-text" lang={text.shown}>
                {text.text}
              </p>
            </li>
          );
        })}
      </ul>
    </Screen>
  );
}
