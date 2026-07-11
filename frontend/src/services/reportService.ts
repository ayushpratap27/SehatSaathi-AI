import api from './api'
import type { Report, ReportListResponse } from '../types'

export const reportService = {
  list: async (limit = 20, offset = 0): Promise<ReportListResponse> => {
    const { data } = await api.get<ReportListResponse>('/reports', {
      params: { limit, offset },
    })
    return data
  },

  get: async (id: string): Promise<Report> => {
    const { data } = await api.get<Report>(`/reports/${id}`)
    return data
  },

  upload: async (file: File, onProgress?: (pct: number) => void): Promise<Report> => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post<Report>('/reports/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
    return data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/reports/${id}`)
  },

  getAnalysis: async (id: string) => {
    const { data } = await api.get(`/reports/${id}/analysis`)
    return data
  },

  getChatHistory: async (id: string) => {
    const { data } = await api.get(`/reports/${id}/chat-history`)
    return data
  },
}
