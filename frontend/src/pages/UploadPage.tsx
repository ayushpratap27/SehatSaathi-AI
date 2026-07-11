import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import { CheckCircle2, FileText, Loader2, Upload, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { reportService } from '../services/reportService'
import Card from '../components/ui/Card'

const MAX_SIZE = 20 * 1024 * 1024
const ACCEPTED = { 'application/pdf': ['.pdf'], 'image/png': ['.png'], 'image/jpeg': ['.jpg', '.jpeg'], 'image/tiff': ['.tiff', '.tif'] }

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export default function UploadPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [file, setFile]         = useState<File | null>(null)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [done, setDone]         = useState(false)
  const [reportId, setReportId] = useState<string | null>(null)

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
      // Invalidate dashboard and reports so they reflect the new upload
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
      <div>
        <h1 className="text-[28px] font-medium text-[#001e2b]">Upload Medical Report</h1>
        <p className="text-[#5c6c7a] mt-1 text-sm">PDF, PNG, JPG, or TIFF · Max 20 MB</p>
      </div>

      <Card>
        <div className="p-6 space-y-5">
          {/* Drop zone */}
          <div
            {...getRootProps()}
            className="rounded-[12px] p-10 text-center cursor-pointer transition-all duration-150"
            style={{
              border: `2px dashed ${isDragActive ? '#00ed64' : '#c1ccd6'}`,
              backgroundColor: isDragActive ? '#e3fcef' : '#f9fbfa',
            }}
          >
            <input {...getInputProps()} />
            <div
              className="w-14 h-14 rounded-[12px] flex items-center justify-center mx-auto mb-4"
              style={{ backgroundColor: isDragActive ? '#00ed64' : '#e1e5e8' }}
            >
              <Upload className="w-7 h-7" style={{ color: isDragActive ? '#001e2b' : '#5c6c7a' }} />
            </div>
            {isDragActive ? (
              <p className="font-semibold text-sm" style={{ color: '#00684a' }}>Drop your file here</p>
            ) : (
              <>
                <p className="font-semibold text-sm text-[#001e2b]">Drag &amp; drop your report here</p>
                <p className="text-xs text-[#a8b3bc] mt-1">or click to browse files</p>
              </>
            )}
          </div>

          {fileRejections.length > 0 && (
            <p className="text-sm text-red-600">{fileRejections[0].errors[0].message}</p>
          )}

          {/* Selected file */}
          {file && !done && (
            <div className="flex items-center gap-3 p-4 rounded-[10px] border border-[#e1e5e8]"
              style={{ backgroundColor: '#f9fbfa' }}>
              <FileText className="w-8 h-8 flex-shrink-0" style={{ color: '#00684a' }} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#001e2b] truncate">{file.name}</p>
                <p className="text-xs text-[#a8b3bc]">{formatBytes(file.size)}</p>
                {uploading && (
                  <div className="mt-2 rounded-full h-1.5 overflow-hidden" style={{ backgroundColor: '#e1e5e8' }}>
                    <div
                      className="h-1.5 rounded-full transition-all"
                      style={{ width: `${progress}%`, backgroundColor: '#00ed64' }}
                    />
                  </div>
                )}
              </div>
              {!uploading && (
                <button onClick={() => setFile(null)} className="text-[#a8b3bc] hover:text-[#5c6c7a] transition-colors">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          )}

          {/* Success */}
          {done && reportId && (
            <div className="flex items-center gap-3 p-4 rounded-[10px] border"
              style={{ backgroundColor: '#e3fcef', borderColor: '#a7f3d0' }}>
              <CheckCircle2 className="w-8 h-8 flex-shrink-0" style={{ color: '#00684a' }} />
              <div>
                <p className="text-sm font-semibold" style={{ color: '#001e2b' }}>Upload complete!</p>
                <p className="text-xs mt-0.5" style={{ color: '#00684a' }}>Your report has been saved and is being processed.</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {!done ? (
              <button onClick={handleUpload} disabled={!file || uploading} className="btn-primary flex items-center gap-2">
                {uploading
                  ? <><Loader2 className="w-4 h-4 animate-spin" />{progress}%</>
                  : <><Upload className="w-4 h-4" />Upload</>}
              </button>
            ) : (
              <>
                <button onClick={() => navigate(`/reports/${reportId}`)} className="btn-primary">View Report</button>
                <button
                  onClick={() => { setFile(null); setDone(false); setReportId(null) }}
                  className="btn-secondary"
                >
                  Upload Another
                </button>
              </>
            )}
          </div>
        </div>
      </Card>

      <p className="text-xs text-[#a8b3bc] text-center">
        For informational purposes only. Always consult a physician.
      </p>
    </div>
  )
}
