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

  if (repLoading) return <div className="flex items-center justify-center h-64"><LoadingSpinner size="lg" /></div>
  if (!report) return <p className="text-slate-500">Report not found.</p>

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 truncate">{report.original_filename}</h1>
          <p className="text-slate-500 text-sm mt-1">
            Uploaded {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
            {report.patient_name && ` · ${report.patient_name}`}
          </p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Link to={`/reports/${id}/chat`} className="btn-primary flex items-center gap-2">
            <MessageCircle className="w-4 h-4" /> Chat
          </Link>
        </div>
      </div>

      {/* Report metadata */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Status',      value: <StatusBadge status={report.status} /> },
          { label: 'File size',   value: `${(report.file_size / 1024).toFixed(1)} KB` },
          { label: 'Type',        value: report.mime_type },
          { label: 'Patient',     value: report.patient_name ?? '—' },
        ].map(({ label, value }) => (
          <Card key={label} className="p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wide mb-1">{label}</p>
            <div className="text-sm font-medium text-slate-800">{value}</div>
          </Card>
        ))}
      </div>

      {/* Analysis section */}
      {analysisLoading ? (
        <Card title="Clinical Analysis"><LoadingSpinner /></Card>
      ) : analysis ? (
        <>
          {/* Summary counts */}
          <Card title="Analysis Overview">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Total Tests',  value: analysis.total_tests,    color: 'text-slate-700' },
                { label: 'Normal',       value: analysis.abnormal_count ? analysis.total_tests - analysis.abnormal_count : 0, color: 'text-green-600' },
                { label: 'Abnormal',     value: analysis.abnormal_count,  color: 'text-amber-600' },
                { label: 'Critical',     value: analysis.critical_count,  color: 'text-red-600' },
              ].map(({ label, value, color }) => (
                <div key={label} className="text-center p-4 bg-slate-50 rounded-xl">
                  <p className={`text-2xl font-bold ${color}`}>{value ?? 0}</p>
                  <p className="text-xs text-slate-500 mt-1">{label}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Structured JSON preview */}
          {analysis.structured_json && (
            <Card title="Extracted Report Data">
              <div className="space-y-3">
                {(() => {
                  try {
                    const d = JSON.parse(analysis.structured_json)
                    return (
                      <>
                        {d.patient?.name && <p className="text-sm text-slate-700"><span className="font-medium">Patient:</span> {d.patient.name}</p>}
                        {d.diagnosis?.length > 0 && (
                          <div>
                            <p className="text-sm font-medium text-slate-700 mb-1">Diagnosis:</p>
                            <ul className="list-disc list-inside space-y-0.5">
                              {d.diagnosis.map((dx: string, i: number) => <li key={i} className="text-sm text-slate-600">{dx}</li>)}
                            </ul>
                          </div>
                        )}
                        {d.tests?.slice(0, 8).map((t: { test_name: string; value: unknown; unit?: string; status?: string }) => (
                          <div key={t.test_name} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                            <span className="text-sm text-slate-700">{t.test_name}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-800">{String(t.value ?? '—')} {t.unit ?? ''}</span>
                              {t.status && <StatusBadge status={t.status} />}
                            </div>
                          </div>
                        ))}
                      </>
                    )
                  } catch { return <p className="text-sm text-slate-500">Could not parse report data.</p> }
                })()}
              </div>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <div className="text-center py-8">
            <FileText className="w-10 h-10 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No analysis stored for this report yet.</p>
            <p className="text-xs text-slate-400 mt-1">Use the API pipeline to extract and analyze this report.</p>
          </div>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-100">
        <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-800">
          Results are for informational purposes only. Consult your healthcare provider for medical interpretation.
        </p>
      </div>
    </div>
  )
}
