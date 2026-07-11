import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity, ChevronDown, FileText, Home, LogOut, Menu, Upload, User, X } from 'lucide-react'
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
    <aside className="flex flex-col h-full" style={{ backgroundColor: '#071C26' }}>
      {/* Logo */}
      <div
        className="flex items-center gap-3 px-4 border-b flex-shrink-0"
        style={{ height: '64px', borderColor: '#0D2C37' }}
      >
        <div
          className="w-9 h-9 rounded-[12px] flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: '#16A34A' }}
        >
          <Activity strokeWidth={2} className="w-[18px] h-[18px] text-white" />
        </div>
        <div className="sidebar-label overflow-hidden">
          <p className="font-bold text-white leading-tight" style={{ fontSize: '16px' }}>SehatSaathi</p>
          <p className="text-[#CBD5E1]" style={{ fontSize: '12px', opacity: 0.8 }}>AI Medical Assistant</p>
        </div>
        <button
          onClick={() => setMobileOpen(false)}
          className="ml-auto text-[#CBD5E1] hover:text-white md:hidden"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-5 px-3 flex flex-col" style={{ gap: '4px' }}>
        {NAV.map(({ to, icon: Icon, label }) => {
          const active = pathname.startsWith(to)
          return (
            <Link
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className="flex items-center rounded-[10px] font-medium transition-all duration-[250ms] sidebar-label"
              style={{
                gap: '10px',
                minHeight: '40px',
                padding: '0 14px',
                fontSize: '14px',
                background: active ? 'linear-gradient(to right, #16A34A, #15803D)' : 'transparent',
                color: active ? '#ffffff' : '#CBD5E1',
              }}
              onMouseEnter={e => { if (!active) (e.currentTarget as HTMLAnchorElement).style.backgroundColor = '#0D2C37' }}
              onMouseLeave={e => { if (!active) (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'transparent' }}
            >
              <Icon strokeWidth={2} className="w-[18px] h-[18px] flex-shrink-0" />
              <span className="sidebar-label">{label}</span>
            </Link>
          )
        })}
      </nav>

      {/* User + Sign out */}
      <div className="px-3 pb-4 border-t flex flex-col" style={{ borderColor: '#0D2C37', gap: '2px', paddingTop: '12px' }}>
        <div className="flex items-center gap-2.5 px-4 py-2">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: '#16A34A' }}
          >
            <span className="text-xs font-bold text-white">{user?.username?.[0]?.toUpperCase() ?? 'U'}</span>
          </div>
          <div className="sidebar-label min-w-0 flex-1">
            <p className="font-semibold text-white truncate" style={{ fontSize: '13px' }}>{user?.username}</p>
            <p className="text-[#CBD5E1] truncate" style={{ fontSize: '11px' }}>{user?.email}</p>
          </div>
          <ChevronDown strokeWidth={2} className="w-3.5 h-3.5 text-[#CBD5E1] sidebar-label flex-shrink-0" />
        </div>
        <button
          onClick={() => logout()}
          className="w-full flex items-center rounded-[10px] text-[#CBD5E1] hover:text-white transition-all duration-[250ms] sidebar-label"
          style={{ gap: '10px', minHeight: '40px', padding: '0 14px', fontSize: '14px', fontWeight: 500 }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#0D2C37' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent' }}
        >
          <LogOut strokeWidth={2} className="w-[18px] h-[18px] flex-shrink-0" />
          <span className="sidebar-label">Sign out</span>
        </button>
      </div>
    </aside>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <div
        className="hidden sm:flex fixed inset-y-0 left-0 z-30 transition-all duration-300"
        style={{ width: 'var(--sidebar-w, 260px)' }}
      >
        {sidebarContent}
      </div>

      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="sm:hidden fixed top-4 left-4 z-40 w-10 h-10 flex items-center justify-center rounded-[14px] text-white shadow-lg"
        style={{ backgroundColor: '#071C26' }}
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile overlay + drawer */}
      {mobileOpen && (
        <div className="sm:hidden fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <div className="relative w-[260px] flex flex-col shadow-xl z-50">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  )
}
