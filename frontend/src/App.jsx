import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import History from './pages/History'
import DocumentDetail from './pages/DocumentDetail'
import Query from './pages/Query'
import Chat from './pages/Chat'
import ResearchDemo from './pages/ResearchDemo'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-100">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/history" element={<History />} />
            <Route path="/document/:docId" element={<DocumentDetail />} />
            <Route path="/research" element={<ResearchDemo />} />
            <Route path="/query" element={<Query />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
