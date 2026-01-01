import apiClient from './index'

// 消息类型
export type MessageRole = 'user' | 'assistant'

// 消息接口
export interface Message {
  id: string
  role: MessageRole
  content: string
  sources: Source[]
  timestamp: string
}

// 引用来源接口
export interface Source {
  id: string
  document_id: string
  document_name: string
  title: string
  content: string
  score: number
}

// 对话接口
export interface Conversation {
  id: string
  title: string
  folderId: string
  createdAt: string
  updatedAt: string
  messages: Message[]
}

// 问答API
export const chatApi = {
  // 提问
  ask: async (
    question: string,
    folderId: string,
    conversationId: string | undefined,
    taskId?: string
  ): Promise<{
    answer: string
    sources: Source[]
  }> => {
    const response = await apiClient.post<{
      answer: string
      sources: Source[]
    }>('/chat/ask', {
      question,
      folderId,
      conversationId,
      taskId
    })
    return response
  },

  // 停止生成
  stopGeneration: async (taskId: string): Promise<{ message: string; taskId: string }> => {
    const response = await apiClient.post<{ message: string; taskId: string }>('/chat/stop', {
      taskId
    })
    return response
  },

  // 创建对话（并发送第一个问题）
  createConversation: async (folderId: string, firstQuestion: string, taskId?: string): Promise<{
    conversationId: string
    answer: string
    sources: Source[]
  }> => {
    const response = await apiClient.post<{
      conversationId: string
      answer: string
      sources: Source[]
    }>('/chat/conversations', {
      folderId,
      firstQuestion,
      taskId
    })
    return response
  },

  // 获取对话列表
  listConversations: async (folderId: string, limit?: number): Promise<{
    conversations: Conversation[]
    total: number
  }> => {
    const response = await apiClient.get<{
      conversations: Conversation[]
      total: number
    }>('/chat/conversations', {
      params: { folderId, limit }
    })
    return response
  },

  // 获取对话详情
  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await apiClient.get<Conversation>(`/chat/conversations/${conversationId}`)
    return response
  },

  // 删除对话
  deleteConversation: async (conversationId: string): Promise<void> => {
    await apiClient.delete(`/chat/conversations/${conversationId}`)
  }
}

