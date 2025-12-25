import { Link, useLocation } from 'react-router-dom'
import { FileText, Upload, BarChart3, Network, Search, MessageSquare, Brain, Beaker } from 'lucide-react'

function Navbar() {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/upload', label: 'Upload', icon: Upload },
    { path: '/history', label: 'Documents', icon: FileText },
    { path: '/research', label: 'Research', icon: Beaker },
    { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  ]
  
  const isActive = (path) => location.pathname === path
  
  return (
    <nav className="bg-slate-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Network className="h-8 w-8 text-blue-400" />
            <span className="font-bold text-xl">DocIntel</span>
          </Link>
          
          <div className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    isActive(item.path)
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
