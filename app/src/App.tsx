import { BrowserRouter, Route, Routes } from 'react-router-dom'
import FarmerPage from './pages/Farmer'
import OfficerPage from './pages/Officer'
import SourcesPage from './pages/Sources'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<FarmerPage />} />
        <Route path="/officer" element={<OfficerPage />} />
        <Route path="/sources" element={<SourcesPage />} />
      </Routes>
    </BrowserRouter>
  )
}
