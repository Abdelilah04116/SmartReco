import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard.tsx'
import Recommendations from './pages/Recommendations.tsx'
import Overview from './pages/Overview.tsx'
import History from './pages/History.tsx'
import ShareView from './pages/ShareView.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
        <Route path="/share/:token" element={<ShareView />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)


