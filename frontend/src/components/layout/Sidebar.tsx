import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity, FileText, Home, LogOut, Menu, Upload, User, X } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '../../context/AuthContext'

const NAV = [
  { to: '/dashboard', icon: Home,     label: 'Dashboard' },
  { to: '/upload',    icon: Upload,   label: 'Upload' },
  { to: '/reports',   icon: FileText, label: 'Reports' },
  { to: '/profile',   icon: User,     label: 'Profile' },
]

export default function Sidebar() {
  const { pathname } = useLocation()
  const { logout, user } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)

  const sidebarContent = (
    <aside
      className={clsx(
        'flex flex-col h-full',
        // Dark MongoDB teal sidebar
        'bg-[#001e2b] text-white',
      )}
    >
      {/* ── Logo ─────────────────────────────── */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-[#1c2d38]">
        <div className="w-9 h-9 rounded-[8px] bg-[#00ed64] flex items-center justify-center flex-shrink-0">
          <Activity className="w-5 h-5 text-[#001e2b]" />
        </div>
        <div className="sidebar-label overflow-hidden">
          <p className="text-sm font-bold text-white leading-tight">SehatSaathi</p>
          <p className="text-[11px] text-[#a8b3bc]">AI Medical Assistant</p>
        </div>
        {/* Mobile close */}
        <button
          onClick={() => setMobileOpen(false)}
          className="ml-auto text-[#a8b3bc] hover:text-white md:hidden"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* ── Navigation ───────────────────────── */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => {
          const active = pathname.startsWith(to)
          return (
            <Link
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={clsx(
                'flex items-center gap-3 rounded-[8px] px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-[#00ed64] text-[#001e2b]'
                  : 'text-[#a8b3bc] hover:bg-[#1c2d38] hover:text-white',
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="sidebar-label">{label}</span>
            </Link>
          )
        })}
      </nav>

      {/* ── User + Logout ─────────────────────── */}
      <div className="px-3 py-4 border-t border-[#1c2d38] space-y-1">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-[#00ed64] flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-bold text-[#001e2b]">
              {user?.username?.[0]?.toUpperCase() ?? 'U'}
            </span>
          </div>
          <div className="sidebar-label min-w-0 flex-1">
            <p className="text-sm font-medium text-white truncate">{user?.username}</p>
            <p className="text-[11px] text-[#a8b3bc] truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={() => logout()}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-[8px] text-sm text-[#a8b3bc] hover:bg-[#1c2d38] hover:text-white transition-colors"
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          <span className="sidebar-label">Sign out</span>
        </button>
      </div>
    </aside>
  )

  return (
    <>
      {/* ── Desktop sidebar ──────────────────────────── */}
      <div className="hidden sm:flex fixed inset-y-0 left-0 z-30 transition-all duration-300"
        style={{ width: 'var(--sidebar-w, 240px)' }}>
        {sidebarContent}
      </div>

      {/* ── Mobile hamburger ─────────────────────────── */}
      <button
        onClick={() => setMobileOpen(true)}
        className="sm:hidden fixed top-4 left-4 z-40 w-9 h-9 flex items-center justify-center rounded-[8px] bg-[#001e2b] text-white shadow-lg"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* ── Mobile overlay + drawer ──────────────────── */}
      {mobileOpen && (
        <div className="sm:hidden fixed inset-0 z-40 flex">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative w-64 flex flex-col shadow-xl z-50">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  )
}
