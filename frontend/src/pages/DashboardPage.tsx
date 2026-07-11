import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, FileText, TrendingUp, Upload } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { chatService } from '../services/analysisService'
import { useAuth } from '../context/AuthContext'
import Card from '../components/ui/Card'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { DashboardStats } from '../types'

function StatCard({ label, value, icon: Icon, accent }: {
  label: string; value: number; icon: React.ElementType; accent: string
}) {
  return (
    <Card className="flex items-center gap-4 p-5">
      <div
        className="w-12 h-12 rounded-[10px] flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: accent + '20', color: accent }}
      >
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-2xl font-semibold text-[#001e2b]">{value}</p>
        <p className="text-sm text-[#5c6c7a]">{label}</p>
      </div>
    </Card>
  )
}

const RISK_STYLE: Record<string, { bg: string; text: string }> = {
  Normal:   { bg: '#e3fcef', text: '#00684a' },
  Low:      { bg: '#e0f2fe', text: '#0369a1' },
  Moderate: { bg: '#fff8e1', text: '#c05600' },
  High:     { bg: '#fff3e0', text: '#b45309' },
  Critical: { bg: '#fee2e2', text: '#b91c1c' },
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

      {/* ── Header ───────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-medium text-[#001e2b] leading-snug">
            Welcome back, {user?.username}
          </h1>
          <p className="text-[#5c6c7a] mt-1 text-sm">Here's an overview of your medical reports.</p>
        </div>
        <Link to="/upload" className="btn-primary flex items-center gap-2 self-start sm:self-auto">
          <Upload className="w-4 h-4" /> Upload Report
        </Link>
      </div>

      {/* ── Stats grid ───────────────────────── */}
      <div className="stats-grid">
        <StatCard label="Total Reports"      value={stats?.total_reports ?? 0}       icon={FileText}     accent="#3b82f6" />
        <StatCard label="Reports This Month" value={stats?.reports_this_month ?? 0}  icon={TrendingUp}   accent="#00ed64" />
        <StatCard label="Completed Analyses" value={stats?.completed_analyses ?? 0}  icon={CheckCircle2} accent="#7b3ff2" />
      </div>

      {/* ── Recent Reports ────────────────────── */}
      <Card title="Recent Reports">
        {!stats?.recent_reports?.length ? (
          <div className="text-center py-14">
            <div className="w-14 h-14 rounded-[12px] bg-[#f4f7f6] flex items-center justify-center mx-auto mb-4">
              <FileText className="w-7 h-7 text-[#a8b3bc]" />
            </div>
            <p className="text-[#5c6c7a] text-sm mb-4">No reports yet.</p>
            <Link to="/upload" className="btn-primary inline-flex">Upload your first report</Link>
          </div>
        ) : (
          <div className="divide-y divide-[#f4f7f6]">
            {stats.recent_reports.map((r) => {
              const rs = r.risk_level ? RISK_STYLE[r.risk_level] : null
              return (
                <div key={r.id} className="flex items-center justify-between py-4 first:pt-0 last:pb-0 gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-[8px] bg-[#f4f7f6] flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-[#a8b3bc]" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[#001e2b] truncate">{r.original_filename}</p>
                      <p className="text-xs text-[#a8b3bc]">
                        {r.patient_name ?? 'Unknown patient'} · {formatDistanceToNow(new Date(r.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    {rs && (
                      <span
                        className="text-xs font-semibold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: rs.bg, color: rs.text }}
                      >
                        {r.risk_level}
                      </span>
                    )}
                    <Link
                      to={`/reports/${r.id}`}
                      className="text-xs font-semibold hover:underline"
                      style={{ color: '#00684a' }}
                    >
                      View →
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>

      {/* ── Disclaimer ────────────────────────── */}
      <div className="flex items-start gap-3 p-4 rounded-[12px] border"
        style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a' }}>
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#d97706' }} />
        <p className="text-sm" style={{ color: '#92400e' }}>
          <strong>Medical Disclaimer:</strong> SehatSaathi-AI is for informational purposes only.
          It does not provide medical diagnoses or prescriptions. Always consult a qualified healthcare professional.
        </p>
      </div>
    </div>
  )
}
