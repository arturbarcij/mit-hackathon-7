import type { Lang } from '../engine';
import { getAnswer } from '../engine';
import { BigButton, CardBlock, Screen } from '../components/Parts';
import { t } from '../ui/strings';

/** Step 3a and 3b: how to pick the leaves, then how to photograph them. One card per screen. */
export function GuidePage({
  lang,
  header,
  step,
  onNext,
}: {
  lang: Lang;
  header: React.ReactNode;
  step: 'pick' | 'photo';
  onNext: () => void;
}) {
  const id = step === 'pick' ? 'how_to_pick_leaves' : 'how_to_photograph';
  return (
    <Screen
      testId={`screen-guide-${step}`}
      header={header}
      footer={<BigButton icon="next" label={t('next', lang)} onClick={onNext} testId="guide-next" />}
    >
      <figure className="guide-figure" aria-hidden="true">
        {step === 'pick' ? <PickPicture /> : <PhotoPicture />}
      </figure>
      <CardBlock card={getAnswer(id)} lang={lang} tone="info" />
    </Screen>
  );
}

/** Ten leaves laid flat on a plain page, underside up. */
function PickPicture() {
  const leaves = Array.from({ length: 10 }, (_, i) => i);
  return (
    <svg viewBox="0 0 220 150" width="100%" height="150" role="img">
      <rect x="10" y="8" width="200" height="134" rx="4" fill="#ffffff" stroke="#1d1d1b" strokeWidth="2" />
      {leaves.map((i) => {
        const x = 32 + (i % 5) * 39;
        const y = 44 + Math.floor(i / 5) * 62;
        return (
          <g key={i} transform={`translate(${x} ${y}) rotate(-35)`}>
            <ellipse rx="16" ry="25" fill="#5b7f4a" stroke="#1d1d1b" strokeWidth="1.5" />
            <line x1="0" y1="-24" x2="0" y2="24" stroke="#1d1d1b" strokeWidth="1.2" />
          </g>
        );
      })}
    </svg>
  );
}

/** One leaf filling the phone screen, in daylight. */
function PhotoPicture() {
  return (
    <svg viewBox="0 0 220 150" width="100%" height="150" role="img">
      <rect x="70" y="6" width="80" height="138" rx="10" fill="#ffffff" stroke="#1d1d1b" strokeWidth="2.5" />
      <rect x="78" y="18" width="64" height="112" fill="#f1efe6" stroke="#1d1d1b" strokeWidth="1" />
      <g transform="translate(110 74) rotate(-30)">
        <ellipse rx="22" ry="46" fill="#5b7f4a" stroke="#1d1d1b" strokeWidth="1.5" />
        <line x1="0" y1="-44" x2="0" y2="44" stroke="#1d1d1b" strokeWidth="1.2" />
      </g>
      <g stroke="#1d1d1b" strokeWidth="2" fill="none">
        <circle cx="190" cy="34" r="12" />
        <path d="M190 12v-6 M190 62v-6 M168 34h-6 M218 34h-6" />
      </g>
    </svg>
  );
}
