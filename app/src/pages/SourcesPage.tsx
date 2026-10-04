import { useState } from 'react'
import { Speak } from '../components/Shell.tsx'
import { getAnswer, textFor } from '../engine/content.ts'
import { clearAll } from '../engine/index.ts'
import { t } from '../i18n.ts'
import { useLang } from '../lang.tsx'

const LINKS = [
  { id: 'S02', href: 'https://fsrp.go.ke/sites/default/files/2025-08/Agriculture%20Extension%20Manual%20v1%20final.pdf' },
  { id: 'S03', href: 'https://www.mdpi.com/2073-4395/11/12/2590' },
  { id: 'S17', href: 'https://infonet-biovision.org/crops-fruits-vegetables/coffee-revised' },
  { id: 'S20', href: 'https://openknowledge.fao.org/handle/20.500.14283/ca7430en' },
  { id: 'S22', href: 'https://data.mendeley.com/datasets/t2r6rszp5c/1' },
  { id: 'S23', href: 'https://data.mendeley.com/datasets/tgv3zb82nd/1' },
  { id: 'S33', href: 'https://power.larc.nasa.gov/' },
]

export function SourcesPage() {
  const { lang } = useLang()
  const [confirming, setConfirming] = useState(false)
  const [deleted, setDeleted] = useState(false)
  const berries = getAnswer('berries_out_of_scope')
  const other = getAnswer('other_crop')

  return (
    <section>
      <h1>{t(lang, 'sources_title')}</h1>
      {['sources_1', 'sources_2', 'sources_3', 'sources_4', 'sources_5', 'sources_6', 'sources_7', 'sources_8'].map((key) => (
        <p key={key} className="lead">
          {t(lang, key)}
        </p>
      ))}
      <ul className="links">
        {LINKS.map((link) => (
          <li key={link.id}>
            <a href={link.href}>{link.id}</a>
          </li>
        ))}
      </ul>
      <h2>{t(lang, 'see_limits')}</h2>
      {berries && (
        <>
          <p className="lead">{textFor(berries, lang)}</p>
          <Speak answerId="berries_out_of_scope" />
        </>
      )}
      {other && <p className="lead">{textFor(other, lang)}</p>}
      <h2>{t(lang, 'delete_all')}</h2>
      {!confirming && (
        <button type="button" className="danger" onClick={() => setConfirming(true)}>
          {t(lang, 'delete_all')}
        </button>
      )}
      {confirming && (
        <button
          type="button"
          className="danger"
          onClick={() => {
            void clearAll().then(() => {
              setDeleted(true)
              setConfirming(false)
            })
          }}
        >
          {t(lang, 'delete_confirm')}
        </button>
      )}
      {deleted && <p className="note">{t(lang, 'deleted')}</p>}
    </section>
  )
}
