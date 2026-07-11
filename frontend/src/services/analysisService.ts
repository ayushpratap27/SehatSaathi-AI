import api from './api'
import type { AISummaryResponse, ExplanationItem, RAGChatResponse } from '../types'

export const analysisService = {
  /** Generate AI executive summary from a structured report + analysis */
  getSummary: async (report: unknown, analysis?: unknown): Promise<AISummaryResponse> => {
    const { data } = await api.post<AISummaryResponse>('/ai/summary', { report, analysis })
    return data
  },

  /** Get plain-language explanations for all entities */
  getExplanations: async (report: unknown, analysis?: unknown): Promise<ExplanationItem[]> => {
    const { data } = await api.post('/ai/explain', { report, analysis })
    return data.explanations ?? []
  },
}

export const chatService = {
  /** Index a document for RAG (call after uploading) */
  indexDocument: async (text: string, documentId: string, sourceFile = ''): Promise<void> => {
    await api.post('/rag/index', { text, document_id: documentId, source_file: sourceFile })
  },

  /** Extract text from report file */
  extractText: async (file: File): Promise<string> => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/report/extract', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data.text ?? ''
  },

  /** Parse report into structured JSON */
  parseReport: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/report/parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /** Run clinical analysis on parsed report */
  analyzeReport: async (parsedReport: unknown) => {
    const { data } = await api.post('/analysis/analyze', parsedReport)
    return data
  },

  /** Ask a question via RAG */
  ragChat: async (
    question: string,
    documentId: string,
    history: Array<{ role: string; content: string }> = [],
    topK = 5,
  ): Promise<RAGChatResponse> => {
    const { data } = await api.post<RAGChatResponse>('/rag/chat', {
      question,
      document_id: documentId,
      conversation_history: history,
      top_k: topK,
    })
    return data
  },

  /** Get dashboard stats */
  getDashboard: async () => {
    const { data } = await api.get('/dashboard')
    return data
  },
}
