// 文档相关类型定义

export type FileType = 'pdf' | 'docx' | 'txt'

export type ParseStatus = 'pending' | 'parsing' | 'success' | 'error'

export interface Document {
  id: string
  title: string
  fileName: string
  fileType: FileType
  fileSize: number
  uploadTime: string
  parsed: boolean
  parseStatus: ParseStatus
  markdownContent?: string
  tags: string[]
  folderId: string
  thumbnail?: string
  errorMessage?: string
}

export interface Folder {
  id: string
  name: string
  parentId: string | null
  createdAt: string
}

export interface DocumentFilter {
  searchQuery: string
  selectedTags: string[]
  currentFolder: string | null
  fileType?: FileType
  parseStatus?: ParseStatus
}

export interface UploadProgress {
  fileName: string
  progress: number
  status: 'uploading' | 'success' | 'error'
}
