import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { StatusBar } from './StatusBar'

export function AppFrame({ children }: { children: ReactNode }) {
  return (
    <main className="app">
      <header className="top">
        <StatusBar />
        <nav className="nav" aria-label="Sections">
          <Link className="btn btn-quiet" to="/">
            Farmer
          </Link>
          <Link className="btn btn-quiet" to="/sources">
            Sources
          </Link>
          <Link className="btn btn-quiet" to="/officer">
            Officer view
          </Link>
        </nav>
      </header>
      <div className="screen">{children}</div>
    </main>
  )
}
