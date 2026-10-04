// Shared building blocks: screen frame, speaker button, big buttons, header badges.
import { useState, type ReactNode } from 'react';
import type { AnswerCard, Lang } from '../engine';
import { cardText } from '../ui/strings';
import { speak } from '../ui/voice';
import { Icon, type IconName } from './Icon';

export function Screen({
  children,
  header,
  footer,
  testId,
}: {
  children: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  testId: string;
}) {
  return (
    <main className="screen" data-testid={testId}>
      {header ? <div className="screen-header">{header}</div> : null}
      <div className="screen-body">{children}</div>
      {footer ? <div className="screen-footer">{footer}</div> : null}
    </main>
  );
}

export function SpeakerButton({
  id,
  lang,
  text,
  textLang,
  label,
  small,
}: {
  id: string | null;
  lang: Lang;
  text: string;
  textLang?: Lang;
  label: string;
  small?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  return (
    <button
      type="button"
      className={`speaker${small ? ' speaker-small' : ''}${busy ? ' speaker-busy' : ''}`}
      aria-label={label}
      onClick={() => {
        setBusy(true);
        void speak(id, lang, text, textLang).finally(() => setTimeout(() => setBusy(false), 600));
      }}
    >
      <Icon name="speaker" size={small ? 26 : 34} />
    </button>
  );
}

/** Answer text with its speaker button, the fallback-language tag and the not-sure line. */
export function CardBlock({
  card,
  lang,
  icon,
  showNotSure = true,
  tone,
  testId,
}: {
  card: AnswerCard;
  lang: Lang;
  icon?: IconName;
  showNotSure?: boolean;
  tone?: string;
  testId?: string;
}) {
  const c = cardText(card, lang);
  return (
    <section className={`card tone-${tone ?? card.severity}`} data-testid={testId ?? `card-${card.id}`} data-card={card.id}>
      <div className="card-row">
        {icon ? (
          <span className="card-icon">
            <Icon name={icon} size={34} />
          </span>
        ) : null}
        <p className="card-text" lang={c.shown}>
          {c.text}
        </p>
        <SpeakerButton id={card.id} lang={lang} text={c.text} textLang={c.shown} label="Play" />
      </div>
      {c.tag ? <p className="tag">{c.tag}</p> : null}
      {showNotSure && c.notSure ? (
        <p className="not-sure" lang={c.shown}>
          <Icon name="question" size={22} /> <span>{c.notSure}</span>
        </p>
      ) : null}
    </section>
  );
}

export function BigButton({
  icon,
  label,
  onClick,
  kind = 'primary',
  disabled,
  testId,
}: {
  icon: IconName;
  label: string;
  onClick: () => void;
  kind?: 'primary' | 'secondary' | 'plain';
  disabled?: boolean;
  testId?: string;
}) {
  return (
    <button type="button" className={`big big-${kind}`} onClick={onClick} disabled={disabled} data-testid={testId}>
      <Icon name={icon} size={30} />
      <span>{label}</span>
    </button>
  );
}

export function TopBar({
  mock,
  offline,
  onBack,
  onHistory,
  backLabel,
  historyLabel,
  mockLabel,
  offlineLabel,
}: {
  mock: boolean;
  offline: 'ready' | 'pending' | 'none';
  onBack?: () => void;
  onHistory?: () => void;
  backLabel: string;
  historyLabel: string;
  mockLabel: string;
  offlineLabel: string;
}) {
  return (
    <div className="topbar">
      {onBack ? (
        <button type="button" className="icon-btn" aria-label={backLabel} onClick={onBack} data-testid="back">
          <Icon name="back" />
        </button>
      ) : (
        <span className="icon-btn-spacer" />
      )}
      <div className="badges">
        {mock ? (
          <span className="badge badge-mock" data-testid="mock-badge">
            {mockLabel}
          </span>
        ) : null}
        {offline !== 'none' ? (
          <span className={`badge badge-${offline}`} data-testid="offline-badge" data-state={offline}>
            {offlineLabel}
          </span>
        ) : null}
      </div>
      {onHistory ? (
        <button type="button" className="icon-btn" aria-label={historyLabel} onClick={onHistory} data-testid="history-btn">
          <Icon name="history" />
        </button>
      ) : (
        <span className="icon-btn-spacer" />
      )}
    </div>
  );
}
