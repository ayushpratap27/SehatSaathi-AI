import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, FileText, MessageCircle, MoreHorizontal, Upload } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { reportService } from '../services/reportService'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { Report } from '../types'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

const STATUS_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  done:       { bg: '#DCFCE7', text: '#16A34A', border: '#BBF7D0' },
  processing: { bg: '#EFF6FF', text: '#2563EB', border: '#BFDBFE' },
  pending:    { bg: '#F8FAFC', text: '#64748B', border: '#E2E8F0' },
  failed:     { bg: '#FEF2F2', text: '#DC2626', border: '#FECACA' },
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
  const total = data?.total ?? 0

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-bold text-[#0F172A]" style={{ fontSize: '48px', lineHeight: '56px' }}>
            My Reports
          </h1>
          <p className="text-[#64748B] mt-1" style={{ fontSize: '20px' }}>
            {total} report{total !== 1 ? 's' : ''} uploaded
          </p>
        </div>
        <Link
          to="/upload"
          className="btn-primary inline-flex items-center gap-2 self-start sm:self-auto"
        >
          <Upload strokeWidth={2} className="w-5 h-5" />
          Upload New
        </Link>
      </div>

      {/* List */}
      {reports.length === 0 ? (
        <div
          className="bg-white border border-[#E5E7EB] rounded-[18px]"
          style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
        >
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-[18px] bg-[#F8FAFC] flex items-center justify-center mx-auto mb-5 border border-[#E5E7EB]">
              <FileText strokeWidth={2} className="w-8 h-8 text-[#94A3B8]" />
            </div>
            <p className="font-semibold text-[#0F172A] mb-1" style={{ fontSize: '20px' }}>No reports yet</p>
            <p className="text-[#64748B] mb-6" style={{ fontSize: '16px' }}>Upload your first medical report to get started.</p>
            <Link to="/upload" className="btn-primary inline-flex items-center gap-2">
              <Upload strokeWidth={2} className="w-5 h-5" />
              Upload Report
            </Link>
          </div>
        </div>
      ) : (
        <div
          className="bg-white border border-[#E5E7EB] rounded-[18px] overflow-hidden"
          style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
        >
          <div className="divide-y divide-[#EEF2F7]">
            {reports.map((r) => {
              const st = STATUS_STYLE[r.status] ?? STATUS_STYLE.pending
              const label = r.status.charAt(0).toUpperCase() + r.status.slice(1)
              return (
                <div
                  key={r.id}
                  className="flex items-center gap-5 px-8 py-5 transition-colors hover:bg-[#F8FAFC]"
                >
                  {/* File icon */}
                  <div className="w-12 h-12 rounded-[12px] flex items-center justify-center flex-shrink-0 border border-[#E5E7EB]" style={{ backgroundColor: '#F8FAFC' }}>
                    <FileText strokeWidth={2} className="w-5 h-5 text-[#94A3B8]" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-[#0F172A] truncate" style={{ fontSize: '18px' }}>
                      {r.original_filename}
                    </p>
                    <p className="text-[#64748B] mt-0.5" style={{ fontSize: '15px' }}>
                      Uploaded {formatDistanceToNow(new Date(r.created_at), { addSuffix: true })}
                      {r.file_size ? <> &nbsp;•&nbsp; {formatBytes(r.file_size)}</> : null}
                    </p>
                  </div>

                  {/* Status badge */}
                  <span
                    className="font-semibold flex-shrink-0"
                    style={{
                      backgroundColor: st.bg,
                      color: st.text,
                      border: `1px solid ${st.border}`,
                      borderRadius: '999px',
                      padding: '5px 14px',
                      fontSize: '14px',
                    }}
                  >
                    {label}
                  </span>

                  {/* Actions */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <Link
                      to={`/reports/${r.id}/chat`}
                      className="w-9 h-9 rounded-[10px] flex items-center justify-center text-[#94A3B8] hover:text-[#16A34A] hover:bg-[#ECFDF5] transition-all"
                      title="Chat with report"
                    >
                      <MessageCircle strokeWidth={2} className="w-5 h-5" />
                    </Link>
                    <Link
                      to={`/reports/${r.id}`}
                      className="inline-flex items-center gap-1 font-semibold text-[#16A34A] hover:text-[#15803D] transition-colors px-3 py-2"
                      style={{ fontSize: '15px', textDecoration: 'none' }}
                    >
                      View <ArrowRight strokeWidth={2} className="w-4 h-4" />
                    </Link>
                    <button className="w-9 h-9 rounded-[10px] flex items-center justify-center text-[#94A3B8] hover:text-[#64748B] hover:bg-[#F8FAFC] transition-all">
                      <MoreHorizontal strokeWidth={2} className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )
            })}
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
          Results are for informational purposes only. Always consult a qualified healthcare professional.
        </p>
      </div>

    </div>
  )
}
