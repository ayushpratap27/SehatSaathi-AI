import { Link } from 'react-router-dom'
import { Activity, Home } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6"
      style={{ backgroundColor: '#001e2b' }}>
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-[20px] bg-[#1c2d38] flex items-center justify-center mx-auto mb-6">
          <Activity className="w-10 h-10 text-[#3d4f5b]" />
        </div>
        <h1 className="text-7xl font-medium mb-2" style={{ color: '#00ed64' }}>404</h1>
        <h2 className="text-xl font-semibold text-white mb-2">Page not found</h2>
        <p className="text-[#a8b3bc] text-sm mb-8">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link to="/dashboard" className="btn-dark inline-flex items-center gap-2 px-6 py-2.5">
          <Home className="w-4 h-4" /> Go to Dashboard
        </Link>
      </div>
    </div>
  )
}
