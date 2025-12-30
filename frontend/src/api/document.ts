import apiClient from './index'
import type { Document, Folder, UploadProgress } from '@/types/document'

export interface UploadResponse {
  documentId: string
  fileName: string
  fileSize: number
}

export interface ParseResponse {
  documentId: string
  markdownContent: string
  images: string[]
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

// 文档 API
export const documentApi = {
  // 上传文档
  upload: async (file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post<UploadResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response
  },

  // 解析文档（启动后台任务）
  parse: async (documentId: string): Promise<{ taskId: string; message: string }> => {
    const response = await apiClient.post<{ taskId: string; message: string }>(`/documents/${documentId}/parse`)
    return response
  },

  // 获取解析状态
  getParseStatus: async (documentId: string): Promise<{ documentId: string; status: string; parsed: boolean }> => {
    const response = await apiClient.get<{ documentId: string; status: string; parsed: boolean }>(`/documents/${documentId}/parse/status`)
    return response
  },

  // 获取文档列表
  list: async (params?: {
    folder?: string
    tag?: string
    search?: string
    page?: number
    pageSize?: number
  }): Promise<DocumentListResponse> => {
    const response = await apiClient.get<DocumentListResponse>('/documents', { params })
    return response
  },

  // 获取文档详情
  get: async (documentId: string): Promise<Document> => {
    const response = await apiClient.get<Document>(`/documents/${documentId}`)
    return response
  },

  // 更新文档
  update: async (documentId: string, data: Partial<Document>): Promise<Document> => {
    const response = await apiClient.put<Document>(`/documents/${documentId}`, data)
    return response
  },

  // 更新文档内容
  updateContent: async (documentId: string, markdownContent: string): Promise<Document> => {
    const response = await apiClient.put<Document>(`/documents/${documentId}/content`, {
      markdownContent,
    })
    return response
  },

  // 删除文档
  delete: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/documents/${documentId}`)
  },

  // 下载文档
  download: async (documentId: string, format: 'pdf' | 'markdown' = 'markdown'): Promise<Blob> => {
    const response = await apiClient.get(`/documents/${documentId}/download`, {
      params: { format },
      responseType: 'blob',
    })
    return response
  },

  // 获取文件夹列表
  listFolders: async (): Promise<Folder[]> => {
    const response = await apiClient.get<Folder[]>('/folders')
    return response
  },

  // 创建文件夹
  createFolder: async (name: string, parentId?: string): Promise<Folder> => {
    const response = await apiClient.post<Folder>('/folders', { name, parentId })
    return response
  },

  // 删除文件夹
  deleteFolder: async (folderId: string): Promise<void> => {
    await apiClient.delete(`/folders/${folderId}`)
  },
}
