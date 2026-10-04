import type { Lang } from '../engine';
import { getAnswer } from '../engine';
import { BigButton, CardBlock, Screen } from '../components/Parts';
import { Icon } from '../components/Icon';
import { t } from '../ui/strings';

/** Step 2: consent_main read aloud. Yes keeps checks on this phone; No stops here. */
export function ConsentPage({
  lang,
  header,
  onYes,
  onNo,
}: {
  lang: Lang;
  header: React.ReactNode;
  onYes: () => void;
  onNo: () => void;
}) {
  return (
    <Screen
      testId="screen-consent"
      header={header}
      footer={
        <div className="row-2">
          <BigButton icon="cross" label={t('no', lang)} kind="secondary" onClick={onNo} testId="consent-no" />
          <BigButton icon="check" label={t('yes', lang)} onClick={onYes} testId="consent-yes" />
        </div>
      }
    >
      <div className="hero-icon">
        <Icon name="lock" size={56} />
      </div>
      <CardBlock card={getAnswer('consent_main')} lang={lang} tone="info" />
    </Screen>
  );
}

export function StoppedPage({ lang, header, onBack }: { lang: Lang; header: React.ReactNode; onBack: () => void }) {
  return (
    <Screen testId="screen-stopped" header={header} footer={<BigButton icon="back" label={t('start_again', lang)} onClick={onBack} />}>
      <div className="hero-icon">
        <Icon name="lock" size={56} />
      </div>
      <CardBlock card={getAnswer('consent_main')} lang={lang} tone="info" />
    </Screen>
  );
}
