import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { AlertCircle, CheckCircle2, FileText, Info, Loader2, Shield, Upload, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { reportService } from '../services/reportService'

const MAX_SIZE = 20 * 1024 * 1024
const ACCEPTED = { 'application/pdf': ['.pdf'], 'image/png': ['.png'], 'image/jpeg': ['.jpg', '.jpeg'], 'image/tiff': ['.tiff', '.tif'] }

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

const FORMAT_BADGES = [
  { label: 'PDF',  bg: '#FEF2F2', color: '#EF4444' },
  { label: 'PNG',  bg: '#EFF6FF', color: '#3B82F6' },
  { label: 'JPG',  bg: '#ECFDF5', color: '#16A34A' },
  { label: 'TIFF', bg: '#F5F3FF', color: '#8B5CF6' },
]

export default function UploadPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [file, setFile]           = useState<File | null>(null)
  const [progress, setProgress]   = useState(0)
  const [uploading, setUploading] = useState(false)
  const [done, setDone]           = useState(false)
  const [reportId, setReportId]   = useState<string | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) { setFile(accepted[0]); setProgress(0); setDone(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop, accept: ACCEPTED, maxSize: MAX_SIZE, maxFiles: 1,
  })

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const report = await reportService.upload(file, setProgress)
      setDone(true)
      setReportId(report.id)
      toast.success('Report uploaded successfully!')
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['reports'] })
    } catch {
      toast.error('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-bold text-[#0F172A]" style={{ fontSize: '26px', lineHeight: '34px' }}>
            Upload Medical Report
          </h1>
          <p className="text-[#64748B] mt-1" style={{ fontSize: '14px' }}>
            Upload your medical report and let SehatSaathi AI analyze it for you.
          </p>
        </div>
        {/* Security badge */}
        <div
          className="flex-shrink-0 hidden sm:flex items-center gap-2.5 bg-white border border-[#E5E7EB] rounded-[14px] px-4 py-3"
          style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
        >
          <div className="w-8 h-8 rounded-[10px] flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#ECFDF5' }}>
            <Shield strokeWidth={2} className="w-4 h-4 text-[#16A34A]" />
          </div>
          <div>
            <p className="font-semibold text-[#0F172A]" style={{ fontSize: '13px' }}>Your data is secure</p>
            <p className="text-[#64748B]" style={{ fontSize: '11px' }}>We don't store your files.</p>
          </div>
        </div>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className="cursor-pointer transition-all duration-[250ms] rounded-[18px] bg-white border-2 border-dashed"
        style={{
          borderColor: isDragActive ? '#16A34A' : '#E5E7EB',
          backgroundColor: isDragActive ? '#ECFDF5' : '#FFFFFF',
          padding: '40px 32px',
          boxShadow: '0 4px 20px rgba(15,23,42,.05)',
        }}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center text-center">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center mb-4"
            style={{ backgroundColor: isDragActive ? '#16A34A' : '#ECFDF5' }}
          >
            <Upload strokeWidth={2} className="w-6 h-6" style={{ color: isDragActive ? '#ffffff' : '#16A34A' }} />
          </div>
          {isDragActive ? (
            <p className="font-bold text-[#16A34A]" style={{ fontSize: '16px' }}>Drop your file here</p>
          ) : (
            <>
              <p className="font-bold text-[#0F172A]" style={{ fontSize: '16px' }}>Drag &amp; drop your report here</p>
              <p className="mt-1" style={{ fontSize: '14px', color: '#64748B' }}>
                or click to{' '}
                <span className="text-[#16A34A] underline underline-offset-2 font-medium">browse files</span>
              </p>
              <p className="mt-3 text-[#94A3B8]" style={{ fontSize: '13px' }}>
                PDF, PNG, JPG, or TIFF &nbsp;•&nbsp; Max 20 MB
              </p>
            </>
          )}
        </div>
      </div>

      {fileRejections.length > 0 && (
        <div className="flex items-center gap-3 px-5 py-4 rounded-[14px] border border-[#FECACA] bg-[#FEF2F2]">
          <AlertCircle strokeWidth={2} className="w-5 h-5 text-[#EF4444] flex-shrink-0" />
          <p className="text-[#DC2626]" style={{ fontSize: '15px' }}>{fileRejections[0].errors[0].message}</p>
        </div>
      )}

      {/* Selected file preview */}
      {file && !done && (
        <div
          className="flex items-center gap-4 bg-white border border-[#E5E7EB] rounded-[18px] px-6 py-5"
          style={{ boxShadow: '0 8px 30px rgba(15,23,42,.05)' }}
        >
          <div className="w-14 h-14 rounded-[14px] flex flex-col items-center justify-center flex-shrink-0 border border-[#FECACA]" style={{ backgroundColor: '#FEF2F2' }}>
            <FileText strokeWidth={2} className="w-6 h-6 text-[#EF4444]" />
            <span className="font-bold text-[#EF4444] tracking-wide" style={{ fontSize: '9px', marginTop: '2px' }}>PDF</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-[#0F172A] truncate" style={{ fontSize: '18px' }}>{file.name}</p>
            <p className="text-[#64748B] mt-0.5" style={{ fontSize: '15px' }}>{formatBytes(file.size)}</p>
            {uploading && (
              <div className="mt-3 rounded-full h-2 overflow-hidden bg-[#E5E7EB]">
                <div
                  className="h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%`, backgroundColor: '#16A34A' }}
                />
              </div>
            )}
          </div>
          {!uploading && (
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null) }}
              className="w-9 h-9 rounded-full flex items-center justify-center text-[#94A3B8] hover:text-[#64748B] hover:bg-[#F8FAFC] transition-all"
            >
              <X strokeWidth={2} className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Success state */}
      {done && reportId && (
        <div
          className="flex items-center gap-4 bg-white border border-[#BBF7D0] rounded-[18px] px-5 py-4"
          style={{ backgroundColor: '#ECFDF5', boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
        >
          <div className="w-10 h-10 rounded-[12px] flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#DCFCE7' }}>
            <CheckCircle2 strokeWidth={2} className="w-5 h-5 text-[#16A34A]" />
          </div>
          <div className="flex-1">
            <p className="font-bold text-[#0F172A]" style={{ fontSize: '14px' }}>Upload complete!</p>
            <p className="text-[#16A34A] mt-0.5" style={{ fontSize: '13px' }}>Your report has been saved and is being processed.</p>
          </div>
        </div>
      )}

      {/* Formats card */}
      <div
        className="flex items-center justify-between bg-white border border-[#E5E7EB] rounded-[18px] px-5 py-4"
        style={{ boxShadow: '0 4px 20px rgba(15,23,42,.05)' }}
      >
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-[12px] flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#ECFDF5' }}>
            <FileText strokeWidth={2} className="w-5 h-5 text-[#16A34A]" />
          </div>
          <div>
            <p className="font-semibold text-[#0F172A] mb-2" style={{ fontSize: '14px' }}>Supported file formats</p>
            <div className="flex flex-wrap items-center gap-1.5">
              {FORMAT_BADGES.map(({ label, bg, color }) => (
                <span
                  key={label}
                  className="font-semibold"
                  style={{ backgroundColor: bg, color, borderRadius: '6px', padding: '2px 8px', fontSize: '12px' }}
                >
                  {label}
                </span>
              ))}
              <span className="text-[#94A3B8]" style={{ fontSize: '12px', marginLeft: '2px' }}>Max file size: 20 MB</span>
            </div>
          </div>
        </div>
        {/* Decorative illustration */}
        <div className="hidden md:flex items-center justify-center w-20 h-16 relative flex-shrink-0">
          <div className="absolute w-12 h-14 rounded-[8px] border-2 border-[#E5E7EB] bg-white" style={{ transform: 'rotate(-8deg)', top: 0, left: 0 }} />
          <div className="absolute w-12 h-14 rounded-[8px] border-2 border-[#E5E7EB] bg-white" style={{ transform: 'rotate(4deg)', top: 2, left: 8 }} />
          <div className="absolute bottom-0 right-0 w-7 h-7 rounded-full flex items-center justify-center" style={{ backgroundColor: '#16A34A' }}>
            <CheckCircle2 strokeWidth={2.5} className="w-4 h-4 text-white" />
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        {!done ? (
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {uploading
              ? <><Loader2 strokeWidth={2} className="w-4 h-4 animate-spin" /> Uploading {progress}%</>
              : <><Upload strokeWidth={2} className="w-4 h-4" /> Upload Report</>}
          </button>
        ) : (
          <>
            <button onClick={() => navigate(`/reports/${reportId}`)} className="btn-primary">
              View Report
            </button>
            <button
              onClick={() => { setFile(null); setDone(false); setReportId(null) }}
              className="inline-flex items-center gap-2 font-semibold text-[#64748B] hover:text-[#0F172A] transition-colors"
              style={{ height: '40px', padding: '0 18px', borderRadius: '10px', fontSize: '14px', border: '1px solid #E5E7EB', backgroundColor: 'white' }}
            >
              Upload Another
            </button>
          </>
        )}
      </div>

      {/* Disclaimer */}
      <div className="flex items-center gap-2 pb-2">
        <Info strokeWidth={2} className="w-4 h-4 text-[#94A3B8] flex-shrink-0" />
        <p className="text-[#94A3B8]" style={{ fontSize: '12px' }}>
          For informational purposes only. Always consult a physician.
        </p>
      </div>

    </div>
  )
}
