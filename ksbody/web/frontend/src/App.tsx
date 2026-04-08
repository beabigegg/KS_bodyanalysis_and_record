import { Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { BarChart3, Database, GitCompareArrows, Gauge, TrendingUp } from 'lucide-react'
import { ImportDetailPage } from './pages/ImportDetailPage'
import { ImportListPage } from './pages/ImportListPage'
import { ComparePage } from './pages/ComparePage'
import { TrendPage } from './pages/TrendPage'
import { R2RPage } from './pages/R2RPage'
import { YieldCorrelationPage } from './pages/YieldCorrelationPage'

const navItems = [
  { to: '/imports', label: 'Recipe Imports', icon: Database },
  { to: '/compare', label: 'Cross-Machine Compare', icon: GitCompareArrows },
  { to: '/trend', label: 'Trend Analysis', icon: TrendingUp },
  { to: '/r2r', label: 'R2R Dashboard', icon: BarChart3 },
  { to: '/yield-correlation', label: 'Yield Correlation', icon: Gauge },
]

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <p className="brand-kicker">KS ConnX Elite</p>
          <h1>Recipe Analysis</h1>
          <p className="brand-meta">FastAPI + React Monolith UI</p>
        </div>
        <nav className="nav-grid">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/imports" replace />} />
          <Route path="/imports" element={<ImportListPage />} />
          <Route path="/imports/:importId" element={<ImportDetailPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/trend" element={<TrendPage />} />
          <Route path="/r2r" element={<R2RPage />} />
          <Route path="/yield-correlation" element={<YieldCorrelationPage />} />
        </Routes>
      </main>
    </div>
  )
}
