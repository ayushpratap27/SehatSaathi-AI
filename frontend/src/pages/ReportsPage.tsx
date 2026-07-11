import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, FileText, MessageCircle, Upload } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { reportService } from '../services/reportService'
import Card from '../components/ui/Card'
import StatusBadge from '../components/ui/StatusBadge'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { Report } from '../types'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export default function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportService.list(50, 0),
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <LoadingSpinner size="lg" />
    </div>
  )

  const reports: Report[] = data?.reports ?? []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Reports</h1>
          <p className="text-slate-500 text-sm mt-1">
            {data?.total ?? 0} report{(data?.total ?? 0) !== 1 ? 's' : ''} uploaded
          </p>
        </div>
        <Link to="/upload" className="btn-primary flex items-center gap-2 px-5 py-2.5">
          <Upload className="w-4 h-4" /> Upload New
        </Link>
      </div>

      {/* List */}
      {reports.length === 0 ? (
        <Card>
          <div className="text-center py-16">
            <FileText className="w-12 h-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No reports yet.</p>
            <Link to="/upload" className="mt-4 inline-flex btn-primary px-5 py-2">
              Upload your first report
            </Link>
          </div>
        </Card>
      ) : (
        <Card noPadding>
          <div className="divide-y divide-slate-50">
            {reports.map((r) => (
              <div key={r.id} className="flex items-center gap-4 px-6 py-4 hover:bg-slate-50 transition-colors">
                {/* Icon */}
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-slate-500" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">{r.original_filename}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {formatDistanceToNow(new Date(r.created_at), { addSuffix: true })}
                    {r.patient_name && ` · ${r.patient_name}`}
                    {' · '}{formatBytes(r.file_size)}
                  </p>
                </div>

                {/* Status */}
                <StatusBadge status={r.status} className="flex-shrink-0" />

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Link
                    to={`/reports/${r.id}/chat`}
                    className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                    title="Chat with this report"
                  >
                    <MessageCircle className="w-4 h-4" />
                  </Link>
                  <Link
                    to={`/reports/${r.id}`}
                    className="text-xs text-green-600 hover:text-green-700 font-medium px-3 py-1.5 rounded-lg hover:bg-green-50 transition-colors"
                  >
                    View →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-100">
        <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-amber-800">
          Results are for informational purposes only. Always consult a qualified healthcare professional.
        </p>
      </div>
    </div>
  )
}
