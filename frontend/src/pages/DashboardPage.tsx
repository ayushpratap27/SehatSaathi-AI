import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, FileText, TrendingUp, Upload } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { chatService } from '../services/analysisService'
import { useAuth } from '../context/AuthContext'
import Card from '../components/ui/Card'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { DashboardStats } from '../types'

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number; icon: React.ElementType; color: string }) {
  return (
    <Card className="flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
      </div>
    </Card>
  )
}

const RISK_COLOR: Record<string, string> = {
  Normal:   'text-green-600 bg-green-50',
  Low:      'text-sky-600 bg-sky-50',
  Moderate: 'text-amber-600 bg-amber-50',
  High:     'text-orange-600 bg-orange-50',
  Critical: 'text-red-600 bg-red-50',
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: chatService.getDashboard,
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <LoadingSpinner size="lg" />
    </div>
  )

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome back, {user?.username} 👋
          </h1>
          <p className="text-slate-500 mt-1 text-sm">Here's an overview of your medical reports.</p>
        </div>
        <Link to="/upload" className="btn-primary flex items-center gap-2 px-5 py-2.5">
          <Upload className="w-4 h-4" /> Upload Report
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Total Reports"       value={stats?.total_reports ?? 0}       icon={FileText}     color="bg-sky-100 text-sky-600" />
        <StatCard label="Reports This Month"  value={stats?.reports_this_month ?? 0}  icon={TrendingUp}   color="bg-green-100 text-green-600" />
        <StatCard label="Completed Analyses"  value={stats?.completed_analyses ?? 0}  icon={CheckCircle2} color="bg-purple-100 text-purple-600" />
      </div>

      {/* Recent Reports */}
      <Card title="Recent Reports">
        {!stats?.recent_reports?.length ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No reports yet.</p>
            <Link to="/upload" className="mt-4 inline-flex btn-primary px-5 py-2">
              Upload your first report
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {stats.recent_reports.map((r) => (
              <div key={r.id} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-slate-500" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{r.original_filename}</p>
                    <p className="text-xs text-slate-400">
                      {r.patient_name ?? 'Unknown patient'} · {formatDistanceToNow(new Date(r.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-4 flex-shrink-0">
                  {r.risk_level && (
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${RISK_COLOR[r.risk_level] ?? 'text-slate-600 bg-slate-100'}`}>
                      {r.risk_level}
                    </span>
                  )}
                  <Link to={`/reports/${r.id}`} className="text-xs text-green-600 hover:text-green-700 font-medium">
                    View →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Medical disclaimer */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-100">
        <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-amber-800">
          <strong>Medical Disclaimer:</strong> SehatSaathi-AI is for informational purposes only.
          It does not provide medical diagnoses or prescriptions. Always consult a qualified healthcare professional.
        </p>
      </div>
    </div>
  )
}
