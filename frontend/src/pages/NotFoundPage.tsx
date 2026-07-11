import { Link } from 'react-router-dom'
import { Activity, Home } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-6">
          <Activity className="w-10 h-10 text-slate-300" />
        </div>
        <h1 className="text-6xl font-bold text-slate-200 mb-2">404</h1>
        <h2 className="text-xl font-semibold text-slate-700 mb-2">Page not found</h2>
        <p className="text-slate-500 text-sm mb-8">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link to="/dashboard" className="inline-flex items-center gap-2 btn-primary px-6 py-2.5">
          <Home className="w-4 h-4" /> Go to Dashboard
        </Link>
      </div>
    </div>
  )
}
