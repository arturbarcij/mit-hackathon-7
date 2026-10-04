import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell.tsx'
import { LangProvider } from './lang.tsx'
import { FarmerFlow } from './pages/FarmerFlow.tsx'
import { HistoryPage } from './pages/HistoryPage.tsx'
import { OfficerPage } from './pages/OfficerPage.tsx'
import { SourcesPage } from './pages/SourcesPage.tsx'

export default function App() {
  return (
    <LangProvider>
      <BrowserRouter>
        <Shell>
          <Routes>
            <Route path="/" element={<FarmerFlow />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/officer" element={<OfficerPage />} />
          </Routes>
        </Shell>
      </BrowserRouter>
    </LangProvider>
  )
}
