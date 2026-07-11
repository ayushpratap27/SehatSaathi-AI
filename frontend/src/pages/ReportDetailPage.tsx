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
    <div className="space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <Link
            to="/reports"
            className="mt-0.5 w-8 h-8 rounded-[10px] flex items-center justify-center flex-shrink-0 border border-[#E5E7EB] bg-white hover:bg-[#F8FAFC] transition-all"
            style={{ boxShadow: '0 2px 8px rgba(15,23,42,.04)' }}
          >
            <ArrowLeft strokeWidth={2} className="w-4 h-4 text-[#64748B]" />
          </Link>
          <div className="min-w-0">
            <h1 className="font-bold text-[#0F172A] truncate" style={{ fontSize: '22px', lineHeight: '30px' }}>
              {report.original_filename}
            </h1>
            <p className="text-[#64748B] mt-0.5" style={{ fontSize: '13px' }}>
              Uploaded {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
              {report.patient_name && ` · ${report.patient_name}`}
            </p>
          </div>
        </div>
        <Link
          to={`/reports/${id}/chat`}
          className="btn-primary inline-flex items-center gap-2 self-start flex-shrink-0"
        >
          <MessageCircle strokeWidth={2} className="w-4 h-4" />
          Chat with Report
        </Link>
      </div>

      {/* Metadata cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          {
            label: 'STATUS',
            icon: FileText,
            iconBg: '#ECFDF5',
            iconColor: '#16A34A',
            value: (
              <span className="inline-flex items-center gap-1 font-bold" style={{ color: st.text, fontSize: '14px' }}>
                {statusLabel}
                {report.status === 'done' && <CheckCircle2 strokeWidth={2.5} className="w-3.5 h-3.5" />}
              </span>
            ),
          },
          {
            label: 'FILE SIZE',
            icon: HardDrive,
            iconBg: '#F5F3FF',
            iconColor: '#8B5CF6',
            value: <span className="font-bold text-[#0F172A]" style={{ fontSize: '14px' }}>{(report.file_size / 1024).toFixed(1)} KB</span>,
          },
          {
            label: 'TYPE',
            icon: FileText,
            iconBg: '#EFF6FF',
            iconColor: '#3B82F6',
            value: <span className="font-bold text-[#0F172A] truncate block" style={{ fontSize: '13px' }}>{report.mime_type}</span>,
          },
          {
            label: 'PATIENT',
            icon: User,
            iconBg: '#FFF7ED',
            iconColor: '#F59E0B',
            value: <span className="font-bold text-[#0F172A]" style={{ fontSize: '14px' }}>{report.patient_name ?? '—'}</span>,
          },
        ].map(({ label, icon: Icon, iconBg, iconColor, value }) => (
          <div
            key={label}
            className="bg-white border border-[#E5E7EB] rounded-[14px] p-4"
            style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-[8px] flex items-center justify-center flex-shrink-0" style={{ backgroundColor: iconBg }}>
                <Icon strokeWidth={2} className="w-3.5 h-3.5" style={{ color: iconColor }} />
              </div>
              <span className="font-semibold text-[#94A3B8] tracking-wide" style={{ fontSize: '11px' }}>{label}</span>
            </div>
            {value}
          </div>
        ))}
      </div>

      {/* Analysis */}
      {analysisLoading ? (
        <div
          className="bg-white border border-[#E5E7EB] rounded-[18px] p-6"
          style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
        >
          <div className="flex items-center gap-2">
            <LoadingSpinner />
            <span className="text-[#64748B]" style={{ fontSize: '14px' }}>Analyzing report…</span>
          </div>
        </div>
      ) : analysis ? (
        <>
          {/* Analysis Overview */}
          <div
            className="bg-white border border-[#E5E7EB] rounded-[18px]"
            style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
          >
            <div className="px-6 border-b border-[#E5E7EB]" style={{ height: '52px', display: 'flex', alignItems: 'center' }}>
              <h2 className="font-semibold text-[#0F172A]" style={{ fontSize: '15px' }}>Analysis Overview</h2>
            </div>
            <div className="p-5">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {ANALYSIS_CARDS.map(({ key, label, bg, color }) => (
                  <div
                    key={key}
                    className="text-center rounded-[12px] py-4 px-3"
                    style={{ backgroundColor: bg }}
                  >
                    <p className="font-bold" style={{ fontSize: '28px', color, lineHeight: 1 }}>{analysisValues[key]}</p>
                    <p className="text-[#64748B] mt-1 font-medium" style={{ fontSize: '13px' }}>{label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Extracted Report Data */}
          {analysis.structured_json && (
            <div
              className="bg-white border border-[#E5E7EB] rounded-[18px]"
              style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
            >
              <div className="px-6 border-b border-[#E5E7EB]" style={{ height: '52px', display: 'flex', alignItems: 'center' }}>
                <h2 className="font-semibold text-[#0F172A]" style={{ fontSize: '15px' }}>Extracted Report Data</h2>
              </div>
              <div className="p-5 space-y-4">
                {(() => {
                  try {
                    const d = JSON.parse(analysis.structured_json)
                    return (
                      <>
                        {d.diagnosis?.length > 0 && (
                          <div>
                            <p className="font-semibold text-[#0F172A] mb-2" style={{ fontSize: '13px' }}>Diagnosis</p>
                            <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1">
                              {d.diagnosis.map((dx: string, i: number) => (
                                <div key={i} className="flex items-start gap-1.5">
                                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#16A34A' }} />
                                  <p className="text-[#64748B]" style={{ fontSize: '13px' }}>{dx}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        {d.tests?.length > 0 && (
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
                                <div key={i} className="flex items-center justify-between py-2.5 gap-3">
                                  <span className="text-[#64748B]" style={{ fontSize: '13px' }}>{t.test_name}</span>
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-[#0F172A]" style={{ fontSize: '13px' }}>
                                      {String(t.value ?? '—')}{t.unit ? ` ${t.unit}` : ''}
                                    </span>
                                    {badge && t.status && (
                                      <span
                                        className="font-semibold flex-shrink-0"
                                        style={{ backgroundColor: badge.bg, color: badge.text, borderRadius: '999px', padding: '2px 8px', fontSize: '11px' }}
                                      >
                                        {t.status.charAt(0).toUpperCase() + t.status.slice(1)}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </>
                    )
                  } catch {
                    return <p className="text-[#94A3B8]" style={{ fontSize: '13px' }}>Could not parse report data.</p>
                  }
                })()}
              </div>
            </div>
          )}
        </>
      ) : (
        <div
          className="bg-white border border-[#E5E7EB] rounded-[18px] p-8"
          style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
        >
          <div className="text-center">
            <div className="w-12 h-12 rounded-[14px] bg-[#F8FAFC] flex items-center justify-center mx-auto mb-4 border border-[#E5E7EB]">
              <FileText strokeWidth={2} className="w-6 h-6 text-[#94A3B8]" />
            </div>
            <p className="font-semibold text-[#0F172A] mb-1" style={{ fontSize: '15px' }}>No analysis available</p>
            <p className="text-[#64748B]" style={{ fontSize: '13px' }}>Use the pipeline to extract and analyze this report.</p>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div
        className="flex items-start gap-4 rounded-[18px] border"
        style={{ backgroundColor: '#FFF8EB', borderColor: '#FCD34D', padding: '16px 20px' }}
      >
        <AlertTriangle strokeWidth={2} className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#F59E0B' }} />
        <p style={{ fontSize: '13px', color: '#0F172A' }}>
          Results are for informational purposes only. Consult your healthcare provider for medical interpretation.
        </p>
      </div>

    </div>
  )
}

