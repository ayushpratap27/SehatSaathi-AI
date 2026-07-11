import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { CheckCircle2, FileText, Loader2, Upload, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { reportService } from '../services/reportService'
import Card from '../components/ui/Card'

const MAX_SIZE = 20 * 1024 * 1024 // 20 MB
const ACCEPTED = { 'application/pdf': ['.pdf'], 'image/png': ['.png'], 'image/jpeg': ['.jpg', '.jpeg'], 'image/tiff': ['.tiff', '.tif'] }

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [done, setDone] = useState(false)
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
    } catch {
      toast.error('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Upload Medical Report</h1>
        <p className="text-slate-500 mt-1 text-sm">PDF, PNG, JPG, or TIFF · Max 20 MB</p>
      </div>

      <Card>
        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-green-500 bg-green-50' : 'border-slate-200 hover:border-green-400 hover:bg-green-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          {isDragActive ? (
            <p className="text-green-600 font-medium">Drop your file here</p>
          ) : (
            <>
              <p className="text-slate-600 font-medium">Drag & drop your report here</p>
              <p className="text-slate-400 text-sm mt-1">or click to browse files</p>
            </>
          )}
        </div>

        {/* File rejection */}
        {fileRejections.length > 0 && (
          <p className="mt-3 text-sm text-red-600">{fileRejections[0].errors[0].message}</p>
        )}

        {/* Selected file */}
        {file && !done && (
          <div className="mt-4 flex items-center gap-3 p-4 bg-slate-50 rounded-xl">
            <FileText className="w-8 h-8 text-green-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
              <p className="text-xs text-slate-500">{formatBytes(file.size)}</p>
              {uploading && (
                <div className="mt-2 bg-slate-200 rounded-full h-1.5">
                  <div className="bg-green-500 h-1.5 rounded-full transition-all" style={{ width: `${progress}%` }} />
                </div>
              )}
            </div>
            {!uploading && <button onClick={() => setFile(null)} className="text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>}
          </div>
        )}

        {/* Success */}
        {done && reportId && (
          <div className="mt-4 p-4 bg-green-50 rounded-xl flex items-center gap-3">
            <CheckCircle2 className="w-8 h-8 text-green-500 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-green-800">Upload complete!</p>
              <p className="text-xs text-green-600 mt-0.5">Your report has been saved.</p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mt-5 flex gap-3">
          {!done ? (
            <button onClick={handleUpload} disabled={!file || uploading} className="btn-primary flex items-center gap-2">
              {uploading ? <><Loader2 className="w-4 h-4 animate-spin" />{progress}%</> : <><Upload className="w-4 h-4" />Upload</>}
            </button>
          ) : (
            <>
              <button onClick={() => navigate(`/reports/${reportId}`)} className="btn-primary">View Report</button>
              <button onClick={() => { setFile(null); setDone(false); setReportId(null) }} className="btn-secondary">Upload Another</button>
            </>
          )}
        </div>
      </Card>

      <p className="text-xs text-slate-400 text-center">
        ⚠️ This tool is for informational purposes only. Always consult a physician.
      </p>
    </div>
  )
}
