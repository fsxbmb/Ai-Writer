import apiClient from './index'

// 文档项目接口定义
export interface DocumentProject {
  id: string
  title: string
  folderIds: string[]
  outline: OutlineNode[] | null
  outlineLocked: boolean
  sections: Record<string, SectionContent>
  createdAt: string
  updatedAt: string
}

export interface OutlineNode {
  id: string
  label: string
  children: OutlineNode[]
}

export interface SectionContent {
  sectionId: string
  paragraphs: Paragraph[]
  sources: Source[]
}

export interface Paragraph {
  id: string
  content: string
  timestamp: string
  versions?: ParagraphVersion[]
}

export interface ParagraphVersion {
  content: string
  timestamp: string
}

export interface Source {
  id: string
  document_id: string
  document_name: string
  title: string
  content: string
  score: number
}

export interface ProjectListResponse {
  projects: DocumentProject[]
  total: number
}

// 文档项目 API
export const documentProjectApi = {
  // 创建项目
  create: async (title: string, folderIds: string[]): Promise<DocumentProject> => {
    const response = await apiClient.post<DocumentProject>('/document-projects', {
      title,
      folderIds,
    })
    return response
  },

  // 获取项目列表
  list: async (skip?: number, limit?: number): Promise<ProjectListResponse> => {
    const response = await apiClient.get<ProjectListResponse>('/document-projects', {
      params: { skip, limit },
    })
    return response
  },

  // 获取项目详情
  get: async (projectId: string): Promise<DocumentProject> => {
    const response = await apiClient.get<DocumentProject>(`/document-projects/${projectId}`)
    return response
  },

  // 更新大纲
  updateOutline: async (
    projectId: string,
    outline: OutlineNode[],
    locked: boolean
  ): Promise<DocumentProject> => {
    const response = await apiClient.put<DocumentProject>(
      `/document-projects/${projectId}/outline`,
      { outline, locked }
    )
    return response
  },

  // 生成大纲
  generateOutline: async (projectId: string, topic: string): Promise<DocumentProject> => {
    const response = await apiClient.post<DocumentProject>(
      `/document-projects/${projectId}/generate-outline`,
      { topic },
      { timeout: 120000 } // 2分钟超时
    )
    return response
  },

  // 删除项目
  delete: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/document-projects/${projectId}`)
  },

  // 生成章节内容
  generateContent: async (
    projectId: string,
    sectionId: string,
    sectionTitle: string,
    contextSections?: string[]
  ): Promise<{
    paragraph_id: string
    section_id: string
    content: string
    sources: Source[]
    timestamp: string
  }> => {
    const response = await apiClient.post<{
      paragraph_id: string
      section_id: string
      content: string
      sources: Source[]
      timestamp: string
    }>(`/document-projects/${projectId}/generate-content`, {
      sectionId,
      sectionTitle,
      contextSections: contextSections || []
    }, { timeout: 120000 })
    return response
  },

  // 重新生成段落
  regenerateParagraph: async (
    projectId: string,
    sectionId: string,
    sectionTitle: string,
    contextSections?: string[],
    customPrompt?: string
  ): Promise<{
    paragraph_id: string
    section_id: string
    content: string
    sources: Source[]
    timestamp: string
    versions?: ParagraphVersion[]
  }> => {
    const response = await apiClient.post<{
      paragraph_id: string
      section_id: string
      content: string
      sources: Source[]
      timestamp: string
      versions?: ParagraphVersion[]
    }>(`/document-projects/${projectId}/regenerate-paragraph`, {
      sectionId,
      sectionTitle,
      contextSections: contextSections || [],
      customPrompt: customPrompt || ''
    }, { timeout: 120000 })
    return response
  },

  // 更新段落内容
  updateParagraph: async (
    projectId: string,
    sectionId: string,
    paragraphId: string,
    content: string
  ): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>(
      `/document-projects/${projectId}/paragraph`,
      { sectionId, paragraphId, content }
    )
    return response
  },

  // 恢复段落版本
  restoreParagraphVersion: async (
    projectId: string,
    sectionId: string,
    paragraphId: string,
    versionIndex: number
  ): Promise<DocumentProject> => {
    const response = await apiClient.post<DocumentProject>(
      `/document-projects/${projectId}/restore-paragraph-version`,
      { sectionId, paragraphId, versionIndex }
    )
    return response
  },

  // 获取项目详情（别名）
  getProject: async (projectId: string): Promise<DocumentProject> => {
    const response = await apiClient.get<DocumentProject>(`/document-projects/${projectId}`)
    return response
  },

  // 导出为 Word 文档
  exportWord: async (projectId: string, title: string = '文档'): Promise<void> => {
    const response = await apiClient.get(`/document-projects/${projectId}/export-word`, {
      responseType: 'blob'
    })

    // 创建下载链接
    const blob = new Blob([response], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${title}.docx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  // 获取预览HTML的URL
  getPreviewHtmlUrl: (projectId: string): string => {
    return `/api/document-projects/${projectId}/preview-html`
  },
}
