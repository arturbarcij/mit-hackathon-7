// Plain line icons, drawn inline so they work offline. 24 x 24 grid, stroke uses currentColor.
export type IconName =
  | 'speaker'
  | 'leaf'
  | 'camera'
  | 'image'
  | 'sample'
  | 'check'
  | 'cross'
  | 'clock'
  | 'person'
  | 'sms'
  | 'history'
  | 'back'
  | 'question'
  | 'spots'
  | 'rust'
  | 'berry'
  | 'lock'
  | 'sun'
  | 'page'
  | 'plus'
  | 'next'
  | 'map'
  | 'house';

const PATHS: Record<IconName, string> = {
  speaker: 'M4 9h4l5-4v14l-5-4H4z M16 9a4 4 0 0 1 0 6 M18.5 6.5a8 8 0 0 1 0 11',
  leaf: 'M5 19C5 10 11 4 20 4c0 9-6 15-15 15z M5 19L14 10',
  camera: 'M3 8h4l2-3h6l2 3h4v11H3z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  image: 'M3 5h18v14H3z M3 16l5-5 4 4 3-3 6 6 M15.5 9.5a1.5 1.5 0 1 0 0-.01',
  sample: 'M4 4h7v7H4z M13 4h7v7h-7z M4 13h7v7H4z M13 13h7v7h-7z',
  check: 'M4 12.5l5 5L20 6.5',
  cross: 'M6 6l12 12 M18 6L6 18',
  clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7v5l3 3',
  person: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21c0-4 3.6-7 8-7s8 3 8 7',
  sms: 'M4 5h16v11H9l-5 4z M8 10h8 M8 13h5',
  history: 'M4 12a8 8 0 1 0 2.3-5.6 M4 4v4h4 M12 8v4l3 2',
  back: 'M15 5l-7 7 7 7',
  question: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14 M12 17.2v.1',
  spots: 'M5 19C5 10 11 4 20 4c0 9-6 15-15 15z M10 13.5a1 1 0 1 0 0-.01 M13.5 10a1 1 0 1 0 0-.01 M14 14.5a1 1 0 1 0 0-.01',
  rust: 'M5 19C5 10 11 4 20 4c0 9-6 15-15 15z M9.5 13a1.8 1.8 0 1 0 0-.01 M14 9.5a1.8 1.8 0 1 0 0-.01 M14.5 14a1.3 1.3 0 1 0 0-.01',
  berry: 'M8 20a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M16 20a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M12 12V6 M12 6c2-2 4-2 6-1',
  lock: 'M6 11h12v9H6z M8.5 11V8a3.5 3.5 0 0 1 7 0v3',
  sun: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M12 2v2 M12 20v2 M2 12h2 M20 12h2 M4.9 4.9l1.4 1.4 M17.7 17.7l1.4 1.4 M4.9 19.1l1.4-1.4 M17.7 6.3l1.4-1.4',
  page: 'M6 3h9l4 4v14H6z M15 3v4h4',
  plus: 'M12 5v14 M5 12h14',
  next: 'M9 5l7 7-7 7',
  map: 'M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z M9 4v14 M15 6v14',
  house: 'M3 11l9-7 9 7 M5 10v10h14V10 M10 20v-6h4v6',
};

export function Icon({ name, size = 28, title }: { name: IconName; size?: number; title?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
    >
      {title ? <title>{title}</title> : null}
      <path d={PATHS[name]} />
    </svg>
  );
}
