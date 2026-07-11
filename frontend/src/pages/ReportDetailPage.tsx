import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, FileText, MessageCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { reportService } from '../services/reportService'
import Card from '../components/ui/Card'
import StatusBadge from '../components/ui/StatusBadge'
import LoadingSpinner from '../components/ui/LoadingSpinner'

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
  if (!report) return <p style={{ color: '#5c6c7a' }}>Report not found.</p>

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Header ───────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-[28px] font-medium text-[#001e2b] truncate">{report.original_filename}</h1>
          <p className="text-[#5c6c7a] text-sm mt-1">
            Uploaded {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
            {report.patient_name && ` · ${report.patient_name}`}
          </p>
        </div>
        <Link to={`/reports/${id}/chat`} className="btn-primary flex items-center gap-2 self-start flex-shrink-0">
          <MessageCircle className="w-4 h-4" /> Chat with Report
        </Link>
      </div>

      {/* ── Metadata grid ──────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Status',    value: <StatusBadge status={report.status} /> },
          { label: 'File size', value: `${(report.file_size / 1024).toFixed(1)} KB` },
          { label: 'Type',      value: report.mime_type },
          { label: 'Patient',   value: report.patient_name ?? '—' },
        ].map(({ label, value }) => (
          <Card key={label} noPadding>
            <div className="p-4">
              <p className="text-[11px] text-[#a8b3bc] uppercase tracking-wider mb-1.5">{label}</p>
              <div className="text-sm font-semibold text-[#001e2b]">{value}</div>
            </div>
          </Card>
        ))}
      </div>

      {/* ── Analysis ─────────────────────────── */}
      {analysisLoading ? (
        <Card title="Clinical Analysis">
          <div className="flex items-center gap-3">
            <LoadingSpinner />
            <span className="text-sm text-[#5c6c7a]">Analyzing…</span>
          </div>
        </Card>
      ) : analysis ? (
        <>
          {/* Overview counts */}
          <Card title="Analysis Overview">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { label: 'Total Tests', value: analysis.total_tests,   color: '#001e2b' },
                { label: 'Normal',      value: analysis.abnormal_count
                    ? analysis.total_tests - analysis.abnormal_count : 0,       color: '#00684a' },
                { label: 'Abnormal',    value: analysis.abnormal_count, color: '#c05600' },
                { label: 'Critical',    value: analysis.critical_count, color: '#b91c1c' },
              ].map(({ label, value, color }) => (
                <div key={label} className="text-center p-4 rounded-[10px]"
                  style={{ backgroundColor: '#f9fbfa' }}>
                  <p className="text-2xl font-semibold" style={{ color }}>{value ?? 0}</p>
                  <p className="text-xs text-[#a8b3bc] mt-1">{label}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Extracted data */}
          {analysis.structured_json && (
            <Card title="Extracted Report Data">
              <div className="space-y-3">
                {(() => {
                  try {
                    const d = JSON.parse(analysis.structured_json)
                    return (
                      <>
                        {d.patient?.name && (
                          <p className="text-sm text-[#001e2b]">
                            <span className="font-medium">Patient:</span> {d.patient.name}
                          </p>
                        )}
                        {d.diagnosis?.length > 0 && (
                          <div>
                            <p className="text-sm font-medium text-[#001e2b] mb-1">Diagnosis:</p>
                            <ul className="list-disc list-inside space-y-0.5">
                              {d.diagnosis.map((dx: string, i: number) => (
                                <li key={i} className="text-sm text-[#5c6c7a]">{dx}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {d.tests?.slice(0, 8).map((t: { test_name: string; value: unknown; unit?: string; status?: string }) => (
                          <div key={t.test_name}
                            className="flex items-center justify-between py-2 border-b last:border-0"
                            style={{ borderColor: '#f4f7f6' }}>
                            <span className="text-sm text-[#5c6c7a]">{t.test_name}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-[#001e2b]">
                                {String(t.value ?? '—')} {t.unit ?? ''}
                              </span>
                              {t.status && <StatusBadge status={t.status} />}
                            </div>
                          </div>
                        ))}
                      </>
                    )
                  } catch {
                    return <p className="text-sm text-[#a8b3bc]">Could not parse report data.</p>
                  }
                })()}
              </div>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <div className="text-center py-6">
            <div className="w-12 h-12 rounded-[10px] bg-[#f4f7f6] flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6 text-[#a8b3bc]" />
            </div>
            <p className="text-[#5c6c7a] text-sm">No analysis stored for this report yet.</p>
            <p className="text-xs text-[#a8b3bc] mt-1">Use the pipeline to extract and analyze this report.</p>
          </div>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="flex items-start gap-3 p-4 rounded-[12px] border"
        style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a' }}>
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: '#d97706' }} />
        <p className="text-xs" style={{ color: '#92400e' }}>
          Results are for informational purposes only. Consult your healthcare provider for medical interpretation.
        </p>
      </div>
    </div>
  )
}
