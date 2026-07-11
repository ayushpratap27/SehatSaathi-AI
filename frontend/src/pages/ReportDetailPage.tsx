import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ArrowLeft, CheckCircle2, FileText, HardDrive, MessageCircle, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { reportService } from '../services/reportService'
import LoadingSpinner from '../components/ui/LoadingSpinner'

const STATUS_STYLE: Record<string, { bg: string; text: string }> = {
  done:       { bg: '#DCFCE7', text: '#16A34A' },
  processing: { bg: '#EFF6FF', text: '#2563EB' },
  pending:    { bg: '#F8FAFC', text: '#64748B' },
  failed:     { bg: '#FEF2F2', text: '#DC2626' },
}

const ANALYSIS_CARDS = [
  { key: 'total',    label: 'Total Tests', bg: '#F8FAFC',  color: '#0F172A' },
  { key: 'normal',   label: 'Normal',      bg: '#ECFDF5',  color: '#16A34A' },
  { key: 'abnormal', label: 'Abnormal',    bg: '#FFF7ED',  color: '#EA580C' },
  { key: 'critical', label: 'Critical',    bg: '#FEF2F2',  color: '#DC2626' },
]

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: report, isLoading: repLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => reportService.get(id!),
    enabled: !!id,
  })

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['report-analysis', id],
    queryFn: () => reportService.getAnalysis(id!),
    enabled: !!id,
    retry: false,
  })

  if (repLoading) return (
    <div className="flex items-center justify-center h-64"><LoadingSpinner size="lg" /></div>
  )
  if (!report) return (
    <div className="text-center py-20">
      <p className="text-[#64748B]" style={{ fontSize: '18px' }}>Report not found.</p>
    </div>
  )

  const st = STATUS_STYLE[report.status] ?? STATUS_STYLE.pending
  const statusLabel = report.status.charAt(0).toUpperCase() + report.status.slice(1)
  const normalCount = analysis
    ? (analysis.total_tests ?? 0) - (analysis.abnormal_count ?? 0)
    : 0

  const analysisValues: Record<string, number> = {
    total:    analysis?.total_tests    ?? 0,
    normal:   normalCount,
    abnormal: analysis?.abnormal_count ?? 0,
    critical: analysis?.critical_count ?? 0,
  }

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-start gap-4 min-w-0">
          <Link
            to="/reports"
            className="mt-1 w-10 h-10 rounded-[12px] flex items-center justify-center flex-shrink-0 border border-[#E5E7EB] bg-white hover:bg-[#F8FAFC] transition-all"
            style={{ boxShadow: '0 2px 8px rgba(15,23,42,.04)' }}
          >
            <ArrowLeft strokeWidth={2} className="w-5 h-5 text-[#64748B]" />
          </Link>
          <div className="min-w-0">
            <h1 className="font-bold text-[#0F172A] truncate" style={{ fontSize: '36px', lineHeight: '44px' }}>
              {report.original_filename}
            </h1>
            <p className="text-[#64748B] mt-1" style={{ fontSize: '18px' }}>
              Uploaded {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
              {report.patient_name && ` · ${report.patient_name}`}
            </p>
          </div>
        </div>
        <Link
          to={`/reports/${id}/chat`}
          className="btn-primary inline-flex items-center gap-2 self-start flex-shrink-0"
        >
          <MessageCircle strokeWidth={2} className="w-5 h-5" />
          Chat with Report
        </Link>
      </div>

      {/* Metadata cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
        {[
          {
            label: 'STATUS',
            icon: FileText,
            iconBg: '#ECFDF5',
            iconColor: '#16A34A',
            value: (
              <span className="inline-flex items-center gap-1.5 font-bold" style={{ color: st.text, fontSize: '18px' }}>
                {statusLabel}
                {report.status === 'done' && <CheckCircle2 strokeWidth={2.5} className="w-4 h-4" />}
              </span>
            ),
          },
          {
            label: 'FILE SIZE',
            icon: HardDrive,
            iconBg: '#F5F3FF',
            iconColor: '#8B5CF6',
            value: <span className="font-bold text-[#0F172A]" style={{ fontSize: '18px' }}>{(report.file_size / 1024).toFixed(1)} KB</span>,
          },
          {
            label: 'TYPE',
            icon: FileText,
            iconBg: '#EFF6FF',
            iconColor: '#3B82F6',
            value: <span className="font-bold text-[#0F172A] truncate block" style={{ fontSize: '16px' }}>{report.mime_type}</span>,
          },
          {
            label: 'PATIENT',
            icon: User,
            iconBg: '#FFF7ED',
            iconColor: '#F59E0B',
            value: <span className="font-bold text-[#0F172A]" style={{ fontSize: '18px' }}>{report.patient_name ?? '—'}</span>,
          },
        ].map(({ label, icon: Icon, iconBg, iconColor, value }) => (
          <div
            key={label}
            className="bg-white border border-[#E5E7EB] rounded-[18px] p-6"
            style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-[10px] flex items-center justify-center flex-shrink-0" style={{ backgroundColor: iconBg }}>
                <Icon strokeWidth={2} className="w-4 h-4" style={{ color: iconColor }} />
              </div>
              <span className="font-semibold text-[#94A3B8] tracking-wide" style={{ fontSize: '12px' }}>{label}</span>
            </div>
            {value}
          </div>
        ))}
      </div>

      {/* Analysis */}
      {analysisLoading ? (
        <div
          className="bg-white border border-[#E5E7EB] rounded-[18px] p-8"
          style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
        >
          <div className="flex items-center gap-3">
            <LoadingSpinner />
            <span className="text-[#64748B]" style={{ fontSize: '16px' }}>Analyzing report…</span>
          </div>
        </div>
      ) : analysis ? (
        <>
          {/* Analysis Overview */}
          <div
            className="bg-white border border-[#E5E7EB] rounded-[18px]"
            style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
          >
            <div className="px-8 border-b border-[#E5E7EB]" style={{ height: '72px', display: 'flex', alignItems: 'center' }}>
              <h2 className="font-bold text-[#0F172A]" style={{ fontSize: '22px' }}>Analysis Overview</h2>
            </div>
            <div className="p-8">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
                {ANALYSIS_CARDS.map(({ key, label, bg, color }) => (
                  <div
                    key={key}
                    className="text-center rounded-[14px] py-6 px-4"
                    style={{ backgroundColor: bg }}
                  >
                    <p className="font-bold" style={{ fontSize: '42px', color, lineHeight: 1 }}>{analysisValues[key]}</p>
                    <p className="text-[#64748B] mt-2 font-medium" style={{ fontSize: '16px' }}>{label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Extracted Report Data */}
          {analysis.structured_json && (
            <div
              className="bg-white border border-[#E5E7EB] rounded-[18px]"
              style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
            >
              <div className="px-8 border-b border-[#E5E7EB]" style={{ height: '72px', display: 'flex', alignItems: 'center' }}>
                <h2 className="font-bold text-[#0F172A]" style={{ fontSize: '22px' }}>Extracted Report Data</h2>
              </div>
              <div className="p-8 space-y-6">
                {(() => {
                  try {
                    const d = JSON.parse(analysis.structured_json)
                    return (
                      <>
                        {d.diagnosis?.length > 0 && (
                          <div>
                            <p className="font-bold text-[#0F172A] mb-3" style={{ fontSize: '18px' }}>Diagnosis</p>
                            <div className="grid sm:grid-cols-2 gap-x-8 gap-y-1.5">
                              {d.diagnosis.map((dx: string, i: number) => (
                                <div key={i} className="flex items-start gap-2">
                                  <span className="mt-1.5 w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: '#16A34A' }} />
                                  <p className="text-[#64748B]" style={{ fontSize: '15px' }}>{dx}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {d.tests?.length > 0 && (
                          <div>
                            <div className="divide-y divide-[#EEF2F7]">
                              {d.tests.map((t: { test_name: string; value: unknown; unit?: string; status?: string }, i: number) => {
                                const testStCustom: Record<string, { bg: string; text: string }> = {
                                  normal:   { bg: '#DCFCE7', text: '#16A34A' },
                                  low:      { bg: '#DBEAFE', text: '#2563EB' },
                                  high:     { bg: '#FEF9C3', text: '#A16207' },
                                  critical: { bg: '#FEE2E2', text: '#DC2626' },
                                }
                                const badge = t.status ? (testStCustom[t.status.toLowerCase()] ?? { bg: '#F8FAFC', text: '#64748B' }) : null
                                return (
                                  <div
                                    key={i}
                                    className="flex items-center justify-between py-4 gap-4"
                                  >
                                    <span className="text-[#64748B]" style={{ fontSize: '16px' }}>{t.test_name}</span>
                                    <div className="flex items-center gap-3">
                                      <span className="font-semibold text-[#0F172A]" style={{ fontSize: '16px' }}>
                                        {String(t.value ?? '—')}{t.unit ? ` ${t.unit}` : ''}
                                      </span>
                                      {badge && t.status && (
                                        <span
                                          className="font-semibold flex-shrink-0"
                                          style={{ backgroundColor: badge.bg, color: badge.text, borderRadius: '999px', padding: '3px 10px', fontSize: '13px' }}
                                        >
                                          {t.status.charAt(0).toUpperCase() + t.status.slice(1)}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </>
                    )
                  } catch {
                    return <p className="text-[#94A3B8]" style={{ fontSize: '16px' }}>Could not parse report data.</p>
                  }
                })()}
              </div>
            </div>
          )}
        </>
      ) : (
        <div
          className="bg-white border border-[#E5E7EB] rounded-[18px] p-12"
          style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
        >
          <div className="text-center">
            <div className="w-16 h-16 rounded-[18px] bg-[#F8FAFC] flex items-center justify-center mx-auto mb-5 border border-[#E5E7EB]">
              <FileText strokeWidth={2} className="w-8 h-8 text-[#94A3B8]" />
            </div>
            <p className="font-semibold text-[#0F172A] mb-1" style={{ fontSize: '20px' }}>No analysis available</p>
            <p className="text-[#64748B]" style={{ fontSize: '16px' }}>Use the pipeline to extract and analyze this report.</p>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div
        className="flex items-start gap-4 rounded-[18px] border"
        style={{ backgroundColor: '#FFF8EB', borderColor: '#FCD34D', padding: '24px 28px' }}
      >
        <AlertTriangle strokeWidth={2} className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#F59E0B' }} />
        <p style={{ fontSize: '16px', color: '#0F172A' }}>
          Results are for informational purposes only. Consult your healthcare provider for medical interpretation.
        </p>
      </div>

    </div>
  )
}

