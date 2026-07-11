import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: '#F8FAFC' }}>
      <Sidebar />
      {/* Offset for sidebar on sm+ screens */}
      <main
        className="flex-1 min-w-0 transition-all duration-300"
        style={{ marginLeft: 'clamp(0px, var(--sidebar-w, 260px), 260px)' }}
      >
        {/* On mobile, add top padding for the hamburger button */}
        <div className="sm:hidden h-14" />
        <div className="page-wrapper">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
