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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-medium text-[#001e2b]">My Reports</h1>
          <p className="text-[#5c6c7a] text-sm mt-1">
            {data?.total ?? 0} report{(data?.total ?? 0) !== 1 ? 's' : ''} uploaded
          </p>
        </div>
        <Link to="/upload" className="btn-primary flex items-center gap-2 self-start sm:self-auto">
          <Upload className="w-4 h-4" /> Upload New
        </Link>
      </div>

      {/* List */}
      {reports.length === 0 ? (
        <Card>
          <div className="text-center py-16">
            <div className="w-14 h-14 rounded-[12px] bg-[#f4f7f6] flex items-center justify-center mx-auto mb-4">
              <FileText className="w-7 h-7 text-[#a8b3bc]" />
            </div>
            <p className="text-[#5c6c7a] text-sm mb-4">No reports yet.</p>
            <Link to="/upload" className="btn-primary inline-flex">Upload your first report</Link>
          </div>
        </Card>
      ) : (
        <Card noPadding>
          <div className="divide-y divide-[#f4f7f6]">
            {reports.map((r) => (
              <div
                key={r.id}
                className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-[#f9fbfa]"
              >
                {/* Icon */}
                <div className="w-10 h-10 rounded-[10px] bg-[#f4f7f6] flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-[#a8b3bc]" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#001e2b] truncate">{r.original_filename}</p>
                  <p className="text-xs text-[#a8b3bc] mt-0.5">
                    {formatDistanceToNow(new Date(r.created_at), { addSuffix: true })}
                    {r.patient_name && ` · ${r.patient_name}`}
                    {' · '}{formatBytes(r.file_size)}
                  </p>
                </div>

                {/* Status */}
                <StatusBadge status={r.status} className="flex-shrink-0" />

                {/* Actions */}
                <div className="flex items-center gap-1 flex-shrink-0">
                  <Link
                    to={`/reports/${r.id}/chat`}
                    className="p-2 rounded-[8px] text-[#a8b3bc] hover:text-[#00684a] hover:bg-[#e3fcef] transition-colors"
                    title="Chat with this report"
                  >
                    <MessageCircle className="w-4 h-4" />
                  </Link>
                  <Link
                    to={`/reports/${r.id}`}
                    className="text-xs font-semibold px-3 py-1.5 rounded-[8px] hover:bg-[#e3fcef] transition-colors"
                    style={{ color: '#00684a' }}
                  >
                    View →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="flex items-start gap-3 p-4 rounded-[12px] border"
        style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a' }}>
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#d97706' }} />
        <p className="text-xs" style={{ color: '#92400e' }}>
          Results are for informational purposes only. Always consult a qualified healthcare professional.
        </p>
      </div>
    </div>
  )
}
