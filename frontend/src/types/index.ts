// ------------------------------------------------------------------ //
// Auth types
// ------------------------------------------------------------------ //

export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterPayload {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface LoginPayload {
  email: string
  password: string
}

// ------------------------------------------------------------------ //
// Report types
// ------------------------------------------------------------------ //

export type ReportStatus = 'pending' | 'processing' | 'done' | 'failed'

export interface Report {
  id: string
  original_filename: string
  saved_filename: string
  file_size: number
  mime_type: string
  status: ReportStatus
  patient_name: string | null
  report_date: string | null
  vector_index_path: string | null
  created_at: string
}

export interface ReportListResponse {
  reports: Report[]
  total: number
  limit: number
  offset: number
}

// ------------------------------------------------------------------ //
// Lab analysis types
// ------------------------------------------------------------------ //

export type TestStatus =
  | 'Normal' | 'Low' | 'High' | 'Very Low' | 'Very High'
  | 'Critical Low' | 'Critical High' | 'Borderline'
  | 'Positive' | 'Negative' | 'Unknown'

export interface LabTest {
  test_name: string
  value: number | string | null
  unit: string | null
  reference_range: string | null
  status: TestStatus
  is_abnormal: boolean
  is_critical: boolean
  insight: string
}

export interface AnalysisSummary {
  total_tests: number
  normal: number
  abnormal: number
  critical: number
  high: number
  low: number
  unknown: number
}

export interface ReportAnalysisResult {
  patient: Record<string, unknown>
  tests: LabTest[]
  analysis: AnalysisSummary
  abnormal_findings: string[]
  critical_findings: string[]
  insights: string[]
  risk_level: 'Normal' | 'Low' | 'Moderate' | 'High' | 'Critical'
  summary: string
  recommendations: string[]
  disclaimer: string
}

// ------------------------------------------------------------------ //
// AI summary types
// ------------------------------------------------------------------ //

export interface AbnormalTestExplanation {
  test_name: string
  value: number | string | null
  unit: string | null
  status: string | null
  explanation: string
}

export interface AISummaryResponse {
  executive_summary: string
  patient_summary: string
  important_findings: string[]
  abnormal_tests: AbnormalTestExplanation[]
  medicines: string[]
  diagnosis: string[]
  follow_up: string[]
  disclaimer: string
  model_used: string
  tokens_used: number | null
}

export interface ExplanationItem {
  term: string
  category: 'lab_test' | 'medicine' | 'diagnosis' | 'medical_term'
  value: string | null
  explanation: string
}

// ------------------------------------------------------------------ //
// RAG / Chat types
// ------------------------------------------------------------------ //

export interface CitationSource {
  page: number | null
  section: string
  score: number
  preview: string
}

export interface RAGChatResponse {
  answer: string
  sources: CitationSource[]
  retrieved_chunks: number
  confidence: number
  disclaimer: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: CitationSource[]
  confidence?: number
  created_at: string
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  created_at: string
}

// ------------------------------------------------------------------ //
// Dashboard types
// ------------------------------------------------------------------ //

export interface RecentReport {
  id: string
  original_filename: string
  status: ReportStatus
  patient_name: string | null
  risk_level: string | null
  created_at: string
}

export interface DashboardStats {
  total_reports: number
  reports_this_month: number
  completed_analyses: number
  recent_reports: RecentReport[]
}

// ------------------------------------------------------------------ //
// API error type
// ------------------------------------------------------------------ //

export interface ApiError {
  success: false
  message: string
  detail?: string
}
