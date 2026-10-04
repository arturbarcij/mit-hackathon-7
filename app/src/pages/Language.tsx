import type { Lang } from '../engine';
import { Icon } from '../components/Icon';
import { Screen } from '../components/Parts';
import { LANGS, languageName } from '../ui/strings';
import { speak } from '../ui/voice';

/** Step 1: tap a speaker to hear each language's name, tap the name to choose it. */
export function LanguagePage({ onPick, header }: { onPick: (l: Lang) => void; header: React.ReactNode }) {
  return (
    <Screen testId="screen-language" header={header}>
      <div className="hero-icon">
        <Icon name="speaker" size={56} />
      </div>
      <ul className="lang-list">
        {LANGS.map((l) => (
          <li key={l} className="lang-row">
            <button
              type="button"
              className="speaker"
              aria-label={`Play ${languageName(l)}`}
              onClick={() => void speak('language_name', l, languageName(l), l)}
            >
              <Icon name="speaker" size={34} />
            </button>
            <button type="button" className="big big-secondary lang-pick" lang={l} onClick={() => onPick(l)} data-testid={`lang-${l}`}>
              <span>{languageName(l)}</span>
            </button>
          </li>
        ))}
      </ul>
    </Screen>
  );
}
