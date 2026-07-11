import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, CheckCircle2, Clock, FileText, TrendingUp, Upload } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { chatService } from '../services/analysisService'
import { useAuth } from '../context/AuthContext'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { DashboardStats } from '../types'

const STAT_ACCENT = {
  blue:   { bg: '#EFF6FF', icon: '#3B82F6' },
  green:  { bg: '#ECFDF5', icon: '#22C55E' },
  purple: { bg: '#F5F3FF', icon: '#8B5CF6' },
}

function StatCard({ label, value, icon: Icon, accent }: {
  label: string
  value: number
  icon: React.ElementType
  accent: { bg: string; icon: string }
}) {
  return (
    <div
      className="relative overflow-hidden bg-white border border-[#E5E7EB] rounded-[18px] transition-all duration-[250ms] hover:-translate-y-0.5"
      style={{ minHeight: '140px', padding: '28px', boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
    >
      <div className="flex items-center gap-5">
        <div
          className="w-16 h-16 rounded-[18px] flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: accent.bg, color: accent.icon }}
        >
          <Icon strokeWidth={2} className="w-[22px] h-[22px]" />
        </div>
        <div>
          <p className="font-bold text-[#0F172A] leading-none" style={{ fontSize: '42px' }}>{value}</p>
          <p className="text-[#64748B] mt-1 font-medium" style={{ fontSize: '20px' }}>{label}</p>
        </div>
      </div>
      {/* Subtle decorative shape */}
      <div
        className="absolute -bottom-4 -right-4 w-32 h-32 rounded-full pointer-events-none"
        style={{ backgroundColor: accent.icon, opacity: 0.06 }}
      />
    </div>
  )
}

const RISK_STYLE: Record<string, { bg: string; text: string }> = {
  Normal:   { bg: '#DCFCE7', text: '#16A34A' },
  Low:      { bg: '#DBEAFE', text: '#2563EB' },
  Moderate: { bg: '#FEF9C3', text: '#A16207' },
  High:     { bg: '#FEE2E2', text: '#DC2626' },
  Critical: { bg: '#FEE2E2', text: '#B91C1C' },
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: chatService.getDashboard,
    staleTime: 30_000, // 30 s — always fresh when navigating back
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <LoadingSpinner size="lg" />
    </div>
  )

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-bold text-[#0F172A]" style={{ fontSize: '48px', lineHeight: '56px' }}>
            Welcome back, {user?.username} 👋
          </h1>
          <p className="text-[#64748B] mt-1" style={{ fontSize: '20px' }}>
            Here's an overview of your medical reports
          </p>
        </div>
        <Link
          to="/upload"
          className="inline-flex items-center gap-2 self-start sm:self-auto text-white font-semibold transition-all duration-[250ms] hover:scale-[1.02] hover:bg-[#15803D]"
          style={{
            backgroundColor: '#16A34A',
            height: '54px',
            padding: '0 28px',
            borderRadius: '14px',
            fontSize: '16px',
            boxShadow: '0 10px 25px rgba(22,163,74,.22)',
            textDecoration: 'none',
          }}
        >
          <Upload strokeWidth={2} className="w-5 h-5" />
          Upload Report
        </Link>
      </div>

      {/* Stats grid */}
      <div className="stats-grid">
        <StatCard label="Total Reports"      value={stats?.total_reports ?? 0}      icon={FileText}     accent={STAT_ACCENT.blue}   />
        <StatCard label="Reports This Month" value={stats?.reports_this_month ?? 0} icon={TrendingUp}   accent={STAT_ACCENT.green}  />
        <StatCard label="Completed Analyses" value={stats?.completed_analyses ?? 0} icon={CheckCircle2} accent={STAT_ACCENT.purple} />
      </div>

      {/* Recent Reports */}
      <div
        className="bg-white border border-[#E5E7EB] rounded-[18px]"
        style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
      >
        <div
          className="flex items-center justify-between px-8 border-b border-[#E5E7EB]"
          style={{ height: '72px' }}
        >
          <h2 className="font-bold text-[#0F172A]" style={{ fontSize: '22px' }}>Recent Reports</h2>
          <Link
            to="/reports"
            className="inline-flex items-center gap-1 font-medium text-[#16A34A] hover:text-[#15803D] transition-colors"
            style={{ fontSize: '16px', textDecoration: 'none' }}
          >
            View all reports <ArrowRight strokeWidth={2} className="w-4 h-4" />
          </Link>
        </div>

        <div className="px-8 py-6" style={{ minHeight: '110px' }}>
          {!stats?.recent_reports?.length ? (
            <div className="text-center py-10">
              <div className="w-14 h-14 rounded-[18px] bg-[#F8FAFC] flex items-center justify-center mx-auto mb-4">
                <FileText className="w-7 h-7 text-[#94A3B8]" />
              </div>
              <p className="text-[#64748B] mb-4" style={{ fontSize: '16px' }}>No reports yet.</p>
              <Link
                to="/upload"
                className="inline-flex items-center gap-2 text-white font-semibold"
                style={{
                  backgroundColor: '#16A34A',
                  height: '46px',
                  padding: '0 24px',
                  borderRadius: '14px',
                  fontSize: '15px',
                  textDecoration: 'none',
                }}
              >
                Upload your first report
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-[#EEF2F7]">
              {stats.recent_reports.map((r) => {
                const rs = r.risk_level ? RISK_STYLE[r.risk_level] : null
                return (
                  <div key={r.id} className="flex items-center justify-between py-5 first:pt-0 last:pb-0 gap-4">
                    <div className="flex items-center gap-4 min-w-0">
                      {/* PDF icon */}
                      <div className="w-14 h-14 rounded-[14px] flex flex-col items-center justify-center flex-shrink-0 border border-[#FECACA]"
                        style={{ backgroundColor: '#FEF2F2' }}>
                        <FileText strokeWidth={2} className="w-6 h-6 text-[#EF4444]" />
                        <span className="font-bold text-[#EF4444] tracking-wide" style={{ fontSize: '9px', marginTop: '2px' }}>PDF</span>
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-[#0F172A] truncate" style={{ fontSize: '22px' }}>
                          {r.original_filename}
                        </p>
                        <p className="text-[#64748B] mt-0.5 flex items-center gap-1" style={{ fontSize: '16px' }}>
                          {r.patient_name ?? 'Unknown patient'}
                          <span className="mx-1">•</span>
                          <Clock strokeWidth={2} className="w-4 h-4 inline flex-shrink-0" />
                          {formatDistanceToNow(new Date(r.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      {rs && (
                        <span
                          className="font-semibold"
                          style={{
                            backgroundColor: rs.bg,
                            color: rs.text,
                            borderRadius: '999px',
                            padding: '6px 14px',
                            fontSize: '14px',
                          }}
                        >
                          {r.risk_level}
                        </span>
                      )}
                      <Link
                        to={`/reports/${r.id}`}
                        className="inline-flex items-center gap-1 font-semibold text-[#16A34A] hover:text-[#15803D] transition-colors"
                        style={{ fontSize: '16px', textDecoration: 'none' }}
                      >
                        View Report <ArrowRight strokeWidth={2} className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Disclaimer */}
      <div
        className="flex items-start gap-4 rounded-[18px] border"
        style={{ backgroundColor: '#FFF8EB', borderColor: '#FCD34D', padding: '28px' }}
      >
        <AlertTriangle strokeWidth={2} className="w-[22px] h-[22px] flex-shrink-0 mt-0.5" style={{ color: '#F59E0B' }} />
        <p style={{ fontSize: '18px', color: '#0F172A' }}>
          <strong style={{ color: '#F59E0B' }}>Medical Disclaimer:</strong>{' '}
          SehatSaathi-AI is for informational purposes only. It does not provide medical diagnoses or prescriptions.
          Always consult a qualified healthcare professional.
        </p>
      </div>

    </div>
  )
}
