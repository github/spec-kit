import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { Home, FileText, MessageSquare, BarChart3, User, LogOut } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) {
    navigate('/login')
    return null
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 glass border-r border-white/20 p-6">
        <h1 className="text-2xl font-bold text-gradient mb-8">PrintMarket</h1>
        <nav className="space-y-2">
          <NavLink to="/dashboard" icon={<Home />}>Dashboard</NavLink>
          <NavLink to="/requests" icon={<FileText />}>Requests</NavLink>
          <NavLink to="/chat" icon={<MessageSquare />}>Chat</NavLink>
          {(user.role === 'ADMIN' || user.role === 'BROKER') && (
            <NavLink to="/analytics" icon={<BarChart3 />}>Analytics</NavLink>
          )}
          <NavLink to="/profile" icon={<User />}>Profile</NavLink>
        </nav>
        <button
          onClick={() => {
            logout()
            navigate('/login')
          }}
          className="mt-8 w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </button>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

function NavLink({ to, icon, children }: any) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/50 transition-all duration-300 text-slate-700 font-medium"
    >
      {icon}
      {children}
    </Link>
  )
}
