<template>
  <div class="chat-view">
    <n-layout has-sider style="height: calc(100vh - 120px)">
      <!-- 左侧：知识库和对话列表 -->
      <n-layout-sider bordered :width="320" content-style="padding: 16px;">
        <n-card size="small" style="margin-bottom: 16px">
          <template #header>
            <n-text strong>选择知识库</n-text>
          </template>
          <n-select
            v-model:value="selectedFolderId"
            :options="folderOptions"
            placeholder="选择要对话的知识库"
            :loading="isLoadingFolders"
            @update:value="handleSelectFolder"
          />
        </n-card>

        <!-- 新建对话按钮 -->
        <n-button
          type="primary"
          block
          size="large"
          @click="handleNewChat"
          :disabled="!selectedFolder"
          style="margin-bottom: 16px"
        >
          <template #icon>
            <n-icon :component="AddIcon" />
          </template>
          新建对话
        </n-button>

        <n-divider style="margin: 16px 0" />

        <n-spin :show="isLoadingConversations">
          <n-list v-if="conversations.length > 0" hoverable clickable>
            <n-list-item
              v-for="conv in conversations"
              :key="conv.id"
              :class="{ 'is-active': currentConversationId === conv.id }"
              @click="handleSelectConversation(conv)"
            >
              <div style="width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <n-text style="flex: 1;">{{ conv.title }}</n-text>
                  <n-button
                    text
                    type="error"
                    size="tiny"
                    @click.stop="handleDeleteConversation(conv)"
                    style="margin-left: 8px;"
                  >
                    <template #icon>
                      <n-icon :component="TrashIcon" />
                    </template>
                  </n-button>
                </div>
                <n-text depth="3" style="font-size: 11px; margin-top: 4px;">
                  {{ formatConversationTime(conv.updatedAt || conv.createdAt) }}
                </n-text>
              </div>
            </n-list-item>
          </n-list>
          <n-empty v-else description="暂无对话" size="small" />
        </n-spin>
      </n-layout-sider>

      <!-- 中间：对话内容展示 -->
      <n-layout content-style="padding: 16px;">
        <n-card v-if="selectedFolder" size="small" style="margin-bottom: 16px;">
          <n-text strong>{{ selectedFolder.name }}</n-text>
          <n-text depth="3" style="margin-left: 12px">({{ documentCount}} 个文档)</n-text>
        </n-card>

        <n-empty v-else description="请先选择一个知识库进行对话" style="margin-top: 100px" />

        <div v-if="selectedFolder" class="messages-container">
          <div v-if="messages.length === 0 && !isLoadingAnswer">
            <n-empty description="开始提问吧" />
          </div>
          <div v-else>
            <div v-for="msg in messages" :key="msg.id" style="margin-bottom: 20px">
              <n-card size="small">
                <n-text depth="3">{{ msg.role === 'user' ? '用户' : 'AI' }}</n-text>
                <n-p>{{ msg.content }}</n-p>
                <div v-if="msg.sources && msg.sources.length > 0" style="margin-top: 12px">
                  <n-divider style="margin: 8px 0" />
                  <n-text depth="3" style="font-size: 12px">引用来源：</n-text>
                  <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 8px;">
                    <n-tag
                      v-for="(source, idx) in msg.sources"
                      :key="source.id"
                      type="info"
                      size="medium"
                      clickable
                      @click="handleViewSource(source)"
                      style="cursor: pointer; justify-content: flex-start; height: auto; padding: 8px 12px;"
                    >
                      <div style="width: 100%;">
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                          <n-text strong style="margin-right: 8px;">[{{ idx + 1 }}]</n-text>
                          <n-text style="font-size: 13px;">{{ source.document_name }}</n-text>
                        </div>
                        <div style="display: flex; align-items: center; margin-left: 24px;">
                          <n-icon :component="DocumentIcon" style="margin-right: 4px; font-size: 14px;" />
                          <n-text depth="3" style="font-size: 12px;">{{ source.title }}</n-text>
                          <n-tag size="tiny" type="info" style="margin-left: auto;">
                            {{ (source.score * 100).toFixed(1) }}%
                          </n-tag>
                        </div>
                      </div>
                    </n-tag>
                  </div>
                </div>
              </n-card>
            </div>

            <!-- 加载动画 -->
            <div v-if="isLoadingAnswer" style="margin-bottom: 20px;">
              <n-card size="small">
                <n-space align="center">
                  <n-spin size="small" />
                  <n-text depth="3">AI 正在思考中...</n-text>
                </n-space>
              </n-card>
            </div>
          </div>
        </div>

        <div v-if="selectedFolder" style="margin-top: 16px;">
          <div style="display: flex; gap: 8px; width: 100%;">
            <n-input
              v-model:value="inputQuestion"
              placeholder="输入问题..."
              @keydown.enter.prevent="handleSend"
              :disabled="isLoadingAnswer"
              style="flex: 1;"
            />
            <n-button
              type="primary"
              @click="handleSend"
              :disabled="!inputQuestion.trim() || isLoadingAnswer"
              :loading="isLoadingAnswer"
            >
              {{ isLoadingAnswer ? '生成中...' : '发送' }}
            </n-button>
          </div>
        </div>
      </n-layout>
    </n-layout>

    <!-- 原文查看抽屉 -->
    <n-drawer v-model:show="showSourceDrawer" :width="800" placement="right">
      <n-drawer-content title="原文片段" closable>
        <template v-if="selectedSource">
          <n-descriptions :column="1" bordered size="small" style="margin-bottom: 16px">
            <n-descriptions-item label="文档名称">
              {{ selectedSource.document_name }}
            </n-descriptions-item>
            <n-descriptions-item label="章节标题">
              {{ selectedSource.title }}
            </n-descriptions-item>
            <n-descriptions-item label="相似度">
              <n-progress
                type="line"
                :percentage="parseFloat((selectedSource.score * 100).toFixed(1))"
                :show-indicator="true"
              />
            </n-descriptions-item>
          </n-descriptions>

          <n-divider />

          <n-card size="small" title="内容">
            <n-p style="white-space: pre-wrap; line-height: 1.8;">
              {{ selectedSource.content }}
            </n-p>
          </n-card>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { documentApi } from '@/api/document'
import { chatApi, type Conversation, type Message, type Source } from '@/api/chat'
import { AddOutline as AddIcon, DocumentOutline as DocumentIcon, TrashOutline as TrashIcon } from '@vicons/ionicons5'

const message = useMessage()
const dialog = useDialog()

const folders = ref<any[]>([])
const selectedFolderId = ref<string | null>(null)
const selectedFolder = ref<any>(null)
const documentCount = ref(0)
const conversations = ref<Conversation[]>([])
const currentConversationId = ref<string | null>(null)
const messages = ref<Message[]>([])
const inputQuestion = ref('')
const isLoadingConversations = ref(false)
const isLoadingFolders = ref(false)
const isLoadingAnswer = ref(false)
const showSourceDrawer = ref(false)
const selectedSource = ref<Source | null>(null)

const folderOptions = computed(() => {
  return folders.value.map(folder => ({
    label: folder.name,
    value: folder.id
  }))
})

async function loadFolders() {
  try {
    isLoadingFolders.value = true
    const result = await documentApi.listFolders()
    folders.value = result
    console.log('Folders loaded:', folders.value.length)
  } catch (error) {
    message.error('加载知识库列表失败')
    console.error(error)
  } finally {
    isLoadingFolders.value = false
  }
}

async function handleSelectFolder(folderId: string) {
  try {
    // 获取知识库信息
    const folder = folders.value.find(f => f.id === folderId)
    if (folder) {
      selectedFolder.value = folder
    }

    // 获取知识库下的文档数量
    const result = await documentApi.list({ folder: folderId })
    documentCount.value = result.documents.length

    currentConversationId.value = null
    messages.value = []
    await loadConversations()
  } catch (error) {
    message.error('加载知识库失败')
    console.error(error)
  }
}

function handleNewChat() {
  if (!selectedFolder.value) {
    message.warning('请先选择知识库')
    return
  }
  currentConversationId.value = null
  messages.value = []
  message.success('已创建新对话')
}

// 格式化对话时间
function formatConversationTime(timestamp: string) {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')

  return `${year}.${month}.${day} ${hour}h${minute}`
}

async function loadConversations() {
  if (!selectedFolder.value) return

  try {
    isLoadingConversations.value = true
    const result = await chatApi.listConversations(selectedFolder.value.id)
    conversations.value = result.conversations
  } catch (error) {
    console.error('加载对话列表失败', error)
  } finally {
    isLoadingConversations.value = false
  }
}

async function handleSelectConversation(conv: Conversation) {
  currentConversationId.value = conv.id
  try {
    const fullConv = await chatApi.getConversation(conv.id)
    messages.value = fullConv.messages
  } catch (error) {
    message.error('加载对话失败')
    console.error(error)
  }
}

async function handleSend() {
  const question = inputQuestion.value.trim()
  if (!question || !selectedFolder.value) return

  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: question,
    sources: [],
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMessage)
  inputQuestion.value = ''

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    isLoadingAnswer.value = true

    let response
    if (currentConversationId.value) {
      response = await chatApi.ask(question, selectedFolder.value.id, currentConversationId.value)
    } else {
      response = await chatApi.createConversation(selectedFolder.value.id, question)
      currentConversationId.value = response.conversationId
      await loadConversations()
    }

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      timestamp: new Date().toISOString()
    }
    messages.value.push(assistantMessage)

    // 调试：打印 sources 数据
    console.log('Sources:', response.sources)

    // 滚动到底部显示新消息
    await nextTick()
    scrollToBottom()
  } catch (error: any) {
    message.error(error.response?.data?.detail || '问答失败')
    console.error(error)
  } finally {
    isLoadingAnswer.value = false
  }
}

function handleViewSource(source: Source) {
  selectedSource.value = source
  showSourceDrawer.value = true
}

async function handleDeleteConversation(conv: Conversation) {
  dialog.warning({
    title: '删除对话',
    content: `确定要删除对话"${conv.title}"吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await chatApi.deleteConversation(conv.id)
        message.success('删除成功')

        // 如果删除的是当前对话，清空消息
        if (currentConversationId.value === conv.id) {
          currentConversationId.value = null
          messages.value = []
        }

        // 重新加载对话列表
        await loadConversations()
      } catch (error: any) {
        message.error(error.response?.data?.detail || '删除失败')
        console.error(error)
      }
    }
  })
}

function scrollToBottom() {
  const container = document.querySelector('.messages-container')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

onMounted(() => {
  console.log('ChatView mounted')
  loadFolders()
})
</script>

<style scoped>
.chat-view {
  height: 100%;
}

/* 对话列表项选中高亮 */
.chat-view :deep(.n-list-item) {
  position: relative;
  transition: all 0.2s;
}

.chat-view :deep(.n-list-item.is-active) {
  background-color: var(--n-color-modal) !important;
  border-radius: 8px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chat-view :deep(.n-list-item.is-active::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--n-color-target);
  border-radius: 8px 0 0 8px;
}
</style>
