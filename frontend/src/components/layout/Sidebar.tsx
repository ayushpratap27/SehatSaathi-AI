import { Link, useLocation } from 'react-router-dom'
import {
  Activity, FileText, Home, LogOut, MessageCircle, Settings, Upload, User,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '../../context/AuthContext'

const NAV = [
  { to: '/dashboard',  icon: Home,          label: 'Dashboard' },
  { to: '/upload',     icon: Upload,         label: 'Upload' },
  { to: '/reports',    icon: FileText,        label: 'Reports',  disabled: true },
  { to: '/profile',    icon: User,           label: 'Profile' },
  { to: '/settings',   icon: Settings,       label: 'Settings', disabled: true },
]

export default function Sidebar() {
  const { pathname } = useLocation()
  const { logout, user } = useAuth()

  return (
    <aside className="fixed inset-y-0 left-0 z-30 w-64 flex flex-col bg-white border-r border-slate-100 shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-100">
        <div className="w-9 h-9 rounded-xl bg-green-600 flex items-center justify-center">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-900">SehatSaathi</p>
          <p className="text-xs text-slate-500">AI Medical Assistant</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {NAV.map(({ to, icon: Icon, label, disabled }) => {
          const active = pathname.startsWith(to) && to !== '/'
          return disabled ? (
            <div key={to} className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-300 cursor-not-allowed select-none">
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium">{label}</span>
              <span className="ml-auto text-xs bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded">Soon</span>
            </div>
          ) : (
            <Link
              key={to}
              to={to}
              className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-green-50 text-green-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* User + Logout */}
      <div className="p-4 border-t border-slate-100 space-y-2">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-semibold text-green-700">
              {user?.username?.[0]?.toUpperCase() ?? 'U'}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.username}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={() => logout()}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  )
}
