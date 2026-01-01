<template>
  <div class="knowledge-view">
    <n-layout has-sider style="height: calc(100vh - 120px)">
      <!-- 左侧知识库列表 -->
      <n-layout-sider
        bordered
        :width="280"
        content-style="padding: 16px;"
      >
        <n-space vertical size="large">
          <!-- 标题和新建按钮 -->
          <n-space justify="space-between" align="center">
            <n-text strong>知识库</n-text>
            <n-button size="small" type="primary" @click="showCreateFolderModal = true">
              <template #icon>
                <n-icon :component="AddIcon" />
              </template>
              新建
            </n-button>
          </n-space>

          <!-- 知识库列表 -->
          <n-list v-if="folders.length > 0" hoverable clickable>
            <n-list-item
              v-for="folder in folders"
              :key="folder.id"
              :class="{ 'is-active': currentFolderId === folder.id }"
              @click="selectFolder(folder.id)"
            >
              <template #prefix>
                <n-icon :component="FolderIcon" />
              </template>
              <n-space vertical :size="4" style="width: 100%">
                <n-space justify="space-between" align="center">
                  <n-text>{{ folder.name }}</n-text>
                  <n-button
                    size="tiny"
                    quaternary
                    type="error"
                    @click.stop="handleDeleteFolder(folder)"
                  >
                    <template #icon>
                      <n-icon :component="TrashIcon" />
                    </template>
                  </n-button>
                </n-space>
                <n-text depth="3" style="font-size: 11px">
                  {{ formatFolderTime(folder.createdAt) }}
                </n-text>
              </n-space>
            </n-list-item>
          </n-list>

          <n-empty v-else description="暂无知识库" size="small">
            <template #extra>
              <n-button size="small" @click="showCreateFolderModal = true">
                创建第一个知识库
              </n-button>
            </template>
          </n-empty>
        </n-space>
      </n-layout-sider>

      <!-- 右侧文档列表 -->
      <n-layout content-style="padding: 16px;">
        <n-space vertical size="large">
          <!-- 顶部工具栏 -->
          <n-space justify="space-between">
            <n-space>
              <n-input
                v-model:value="searchQuery"
                placeholder="搜索文档..."
                clearable
                style="width: 300px"
                @input="handleSearch"
              >
                <template #prefix>
                  <n-icon :component="SearchIcon" />
                </template>
              </n-input>
            </n-space>

            <n-space>
              <n-tooltip :disabled="!!currentFolderId" placement="bottom">
                <template #trigger>
                  <n-button
                    type="info"
                    :disabled="!currentFolderId"
                    :loading="batchVectorizingFolders.includes(currentFolderId || '')"
                    @click="showBatchVectorizeModal = true"
                  >
                    <template #icon>
                      <n-icon :component="GridIcon" />
                    </template>
                    批量向量化
                  </n-button>
                </template>
                请先选择一个知识库
              </n-tooltip>
              <n-tooltip :disabled="!!currentFolderId" placement="bottom">
                <template #trigger>
                  <n-button
                    type="primary"
                    :disabled="!currentFolderId"
                    @click="handleUploadClick"
                  >
                    <template #icon>
                      <n-icon :component="UploadIcon" />
                    </template>
                    上传文档
                  </n-button>
                </template>
                请先选择一个知识库
              </n-tooltip>
            </n-space>
          </n-space>

          <!-- 当前知识库信息 -->
          <n-card v-if="currentFolder" size="small">
            <n-space>
              <n-icon :component="FolderIcon" />
              <n-text strong>{{ currentFolder.name }}</n-text>
              <n-text depth="3">
                {{ filteredDocuments.length }} 个文档
              </n-text>
            </n-space>
          </n-card>

          <!-- 文档列表 -->
          <n-spin :show="isLoading">
            <div v-if="!currentFolderId" class="empty-state">
              <n-empty description="请选择或创建一个知识库">
                <template #icon>
                  <n-icon :component="FolderOpenIcon" />
                </template>
                <template #extra>
                  <n-button type="primary" @click="showCreateFolderModal = true">
                    创建知识库
                  </n-button>
                </template>
              </n-empty>
            </div>

            <div v-else-if="filteredDocuments.length === 0" class="empty-state">
              <n-empty description="此知识库暂无文档">
                <template #icon>
                  <n-icon :component="DocumentIcon" />
                </template>
                <template #extra>
                  <n-button type="primary" @click="handleUploadClick">
                    上传第一个文档
                  </n-button>
                </template>
              </n-empty>
            </div>

            <div v-else class="document-list">
              <div
                v-for="doc in filteredDocuments"
                :key="doc.id"
                class="document-item"
                @click="handleViewDocument(doc)"
              >
                <n-space justify="space-between" align="center" style="width: 100%">
                  <n-space align="center">
                    <n-text>{{ doc.title }}</n-text>
                  </n-space>

                  <n-space align="center">
                    <n-space :size="4">
                      <n-tag
                        :type="doc.parsed ? 'success' : 'default'"
                        size="small"
                        :bordered="false"
                      >
                        {{ doc.parsed ? '已解析' : '待解析' }}
                      </n-tag>
                      <n-tag
                        v-if="doc.parsed && doc.chunked"
                        type="info"
                        size="small"
                        :bordered="false"
                      >
                        已分块
                      </n-tag>
                    </n-space>
                    <n-text depth="3" style="font-size: 12px">
                      {{ formatTime(doc.uploadTime) }}
                    </n-text>
                    <n-button
                      size="tiny"
                      quaternary
                      type="error"
                      class="delete-btn"
                      @click.stop="handleDeleteDocument(doc)"
                    >
                      <template #icon>
                        <n-icon :component="TrashIcon" />
                      </template>
                    </n-button>
                  </n-space>
                </n-space>
              </div>
            </div>
          </n-spin>
        </n-space>
      </n-layout>
    </n-layout>

    <!-- 新建知识库对话框 -->
    <n-modal v-model:show="showCreateFolderModal" preset="card" title="新建知识库" style="width: 500px">
      <n-input
        v-model:value="newFolderName"
        placeholder="请输入知识库名称"
        @keydown.enter="handleCreateFolder"
      />
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateFolderModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreateFolder">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 上传文档对话框 -->
    <n-modal v-model:show="showUploadModal" preset="card" title="上传文档" style="width: 600px">
      <n-space vertical>
        <n-form-item label="选择目标知识库" label-placement="top" required>
          <n-select
            v-model:value="selectedFolderForUpload"
            :options="folderOptions"
            placeholder="请选择知识库"
          />
        </n-form-item>

        <n-alert v-if="selectedFolderForUpload" type="info" :closable="false">
          将上传到：<strong>{{ getFolderName(selectedFolderForUpload) }}</strong>
        </n-alert>

        <n-spin :show="isUploading">
          <file-uploader :disabled="!selectedFolderForUpload" @upload="handleUpload" />
        </n-spin>
      </n-space>
    </n-modal>

    <!-- 批量向量化模式选择对话框 -->
    <n-modal v-model:show="showBatchVectorizeModal" preset="card" title="批量向量化" style="width: 500px">
      <n-space vertical size="large">
        <n-alert type="info" :closable="false">
          知识库：<strong>{{ currentFolder?.name }}</strong>
        </n-alert>

        <n-text>请选择批量向量化的处理模式：</n-text>

        <n-space vertical :size="16">
          <div
            class="mode-option"
            :class="{ 'is-selected': batchVectorizeMode === 'incremental' }"
            @click="batchVectorizeMode = 'incremental'"
          >
            <n-radio :checked="batchVectorizeMode === 'incremental'" @update:checked="batchVectorizeMode = 'incremental'">
              <n-space vertical :size="4">
                <n-text strong>增量处理（推荐）</n-text>
                <n-text depth="3" style="font-size: 12px">
                  只处理未向量化的文档，保留已完成的处理结果
                </n-text>
              </n-space>
            </n-radio>
          </div>

          <div
            class="mode-option"
            :class="{ 'is-selected': batchVectorizeMode === 'full' }"
            @click="batchVectorizeMode = 'full'"
          >
            <n-radio :checked="batchVectorizeMode === 'full'" @update:checked="batchVectorizeMode = 'full'">
              <n-space vertical :size="4">
                <n-text strong>清空重建</n-text>
                <n-text depth="3" style="font-size: 12px">
                  删除所有现有的分块和向量化结果，重新处理所有文档
                </n-text>
              </n-space>
            </n-radio>
          </div>
        </n-space>

        <n-alert v-if="batchVectorizeMode === 'full'" type="warning" :closable="false">
          警告：清空重建将删除所有现有的分块和向量化结果，此操作不可恢复！
        </n-alert>
      </n-space>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showBatchVectorizeModal = false">取消</n-button>
          <n-button type="primary" @click="handleBatchVectorizeCurrentFolder">
            开始处理
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 文档详情抽屉 -->
    <n-drawer v-model:show="showDocumentDrawer" :width="1200" placement="right">
      <template #header>
        <n-space align="center">
          <n-icon :component="FileIcon" />
          <n-text strong>{{ selectedDocument?.title }}</n-text>
        </n-space>
      </template>

      <n-tabs type="line" animated>
        <n-tab-pane name="pdf" tab="PDF 预览">
          <div v-if="selectedDocument" class="pdf-viewer-container">
            <iframe
              :src="`/api/documents/${selectedDocument.id}/download?format=pdf`"
              class="pdf-iframe"
              type="application/pdf"
            ></iframe>
          </div>
        </n-tab-pane>

        <n-tab-pane name="content" tab="解析内容">
          <div v-if="selectedDocument && selectedDocument.markdownContent" class="markdown-content">
            <div v-html="selectedDocument.markdownContent"></div>
          </div>
          <n-empty v-else description="暂无解析内容" />
        </n-tab-pane>

        <n-tab-pane name="info" tab="文档信息">
          <n-descriptions v-if="selectedDocument" :column="2" bordered>
            <n-descriptions-item label="文档标题">
              {{ selectedDocument.title }}
            </n-descriptions-item>
            <n-descriptions-item label="文件名">
              {{ selectedDocument.fileName }}
            </n-descriptions-item>
            <n-descriptions-item label="文件类型">
              {{ selectedDocument.fileType.toUpperCase() }}
            </n-descriptions-item>
            <n-descriptions-item label="文件大小">
              {{ formatFileSize(selectedDocument.fileSize) }}
            </n-descriptions-item>
            <n-descriptions-item label="上传时间">
              {{ formatFullTime(selectedDocument.uploadTime) }}
            </n-descriptions-item>
            <n-descriptions-item label="解析状态">
              <n-tag
                :type="selectedDocument.parsed ? 'success' : 'warning'"
                size="small"
              >
                {{ selectedDocument.parsed ? '已解析' : '待解析' }}
              </n-tag>
            </n-descriptions-item>
          </n-descriptions>
        </n-tab-pane>
      </n-tabs>

      <template #footer>
        <n-space justify="space-between">
          <n-space>
            <n-button
              v-if="selectedDocument && !selectedDocument.parsed"
              type="primary"
              @click="handleParse(selectedDocument)"
            >
              解析文档
            </n-button>
          </n-space>
          <n-button @click="showDocumentDrawer = false">关闭</n-button>
        </n-space>
      </template>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useDocumentStore } from '@/stores/document'
import type { Document, Folder } from '@/types/document'
import { documentApi } from '@/api/document'
import {
  SearchOutline as SearchIcon,
  CloudUploadOutline as UploadIcon,
  FolderOutline as FolderIcon,
  FolderOpenOutline as FolderOpenIcon,
  DocumentTextOutline as DocumentIcon,
  AddOutline as AddIcon,
  DocumentOutline as FileIcon,
  TrashOutline as TrashIcon,
  GridOutline as GridIcon,
} from '@vicons/ionicons5'
import FileUploader from '@/components/knowledge/FileUploader.vue'

const message = useMessage()
const router = useRouter()
const documentStore = useDocumentStore()

const searchQuery = ref('')
const showCreateFolderModal = ref(false)
const showUploadModal = ref(false)
const newFolderName = ref('')
const currentFolderId = ref<string | null>(null)
const selectedFolderForUpload = ref<string | null>(null)
const isLoading = ref(false)
const isUploading = ref(false)
const showDocumentDrawer = ref(false)
const selectedDocument = ref<Document | null>(null)
const batchVectorizingFolders = ref<string[]>([])
const showBatchVectorizeModal = ref(false)
const batchVectorizeMode = ref<'incremental' | 'full'>('incremental')

const folders = computed(() => documentStore.folders.filter((f) => f.id !== 'root'))
const currentFolder = computed(() =>
  documentStore.folders.find((f) => f.id === currentFolderId.value)
)
const filteredDocuments = computed(() => documentStore.filteredDocuments)

const folderOptions = computed(() =>
  folders.value.map((f) => ({ label: f.name, value: f.id }))
)

function getFolderName(folderId: string | null) {
  if (!folderId) return ''
  const folder = folders.value.find((f) => f.id === folderId)
  return folder?.name || ''
}

function formatFolderTime(timestamp: string) {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')

  return `${year}.${month}.${day} ${hour}h${minute}`
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return date.toLocaleDateString('zh-CN')
}

async function selectFolder(folderId: string) {
  currentFolderId.value = folderId
  documentStore.setCurrentFolder(folderId)
  await loadDocuments()
}

function handleSearch(query: string) {
  documentStore.updateFilter({ searchQuery: query })
}

function handleViewDocument(doc: Document) {
  router.push({ name: 'DocumentPreview', params: { id: doc.id } })
}

function formatFullTime(timestamp: string) {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatFileSize(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

async function handleParse(doc: Document) {
  try {
    await documentApi.parse(doc.id)
    message.success('开始解析文档')
    await loadDocuments()
    // 刷新当前文档信息
    const updatedDoc = await documentApi.get(doc.id)
    selectedDocument.value = updatedDoc
  } catch (error) {
    message.error('解析失败')
  }
}

async function loadDocuments() {
  try {
    isLoading.value = true
    const result = await documentApi.list({
      folder: currentFolderId.value || undefined,
    })
    documentStore.setDocuments(result.documents)
  } catch (error) {
    message.error('加载文档列表失败')
  } finally {
    isLoading.value = false
  }
}

async function loadFolders() {
  try {
    const folderList = await documentApi.listFolders()
    documentStore.setFolders(folderList)

    if (folderList.length > 0 && !currentFolderId.value) {
      const userFolder = folderList.find((f) => f.id !== 'root')
      if (userFolder) {
        selectFolder(userFolder.id)
      }
    }
  } catch (error) {
    message.error('加载知识库列表失败')
  }
}

async function handleCreateFolder() {
  if (!newFolderName.value.trim()) {
    message.warning('请输入知识库名称')
    return
  }

  try {
    const folder = await documentApi.createFolder(newFolderName.value)
    documentStore.addFolder(folder)
    showCreateFolderModal.value = false
    newFolderName.value = ''
    message.success('知识库创建成功')

    selectFolder(folder.id)
  } catch (error) {
    message.error('创建知识库失败')
  }
}

function handleUploadClick() {
  selectedFolderForUpload.value = currentFolderId.value
  showUploadModal.value = true
}

async function handleUpload(file: File) {
  if (!selectedFolderForUpload.value) {
    message.error('请选择目标知识库')
    return
  }

  try {
    isUploading.value = true

    const formData = new FormData()
    formData.append('file', file)
    formData.append('folderId', selectedFolderForUpload.value)

    const response = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error('上传失败')
    }

    message.success('上传成功')
    showUploadModal.value = false
    selectedFolderForUpload.value = null

    await loadDocuments()
  } catch (error) {
    console.error('上传错误:', error)
    message.error('上传失败')
  } finally {
    isUploading.value = false
  }
}

async function handleDeleteDocument(doc: Document) {
  if (!confirm(`确定要删除文档"${doc.title}"吗？此操作不可恢复。`)) {
    return
  }

  try {
    await documentApi.delete(doc.id)
    message.success('删除成功')

    // 如果删除的是当前打开的文档，关闭抽屉
    if (selectedDocument.value?.id === doc.id) {
      showDocumentDrawer.value = false
      selectedDocument.value = null
    }

    await loadDocuments()
  } catch (error) {
    message.error('删除失败')
  }
}

async function handleDeleteFolder(folder: Folder) {
  if (!confirm(`确定要删除知识库"${folder.name}"吗？此操作将同时删除该知识库下的所有文档，且不可恢复。`)) {
    return
  }

  try {
    await documentApi.deleteFolder(folder.id)
    message.success('知识库删除成功')

    // 如果删除的是当前选中的知识库，清空选择
    if (currentFolderId.value === folder.id) {
      currentFolderId.value = null
      documentStore.setCurrentFolder(null)
      documentStore.setDocuments([])
    }

    await loadFolders()
  } catch (error) {
    message.error('删除失败')
  }
}

async function handleBatchVectorizeCurrentFolder() {
  if (!currentFolderId.value) {
    message.warning('请先选择一个知识库')
    return
  }

  const folder = folders.value.find(f => f.id === currentFolderId.value)
  if (!folder) return

  try {
    // 关闭对话框
    showBatchVectorizeModal.value = false

    // 添加到正在向量化的列表
    batchVectorizingFolders.value = [...batchVectorizingFolders.value, folder.id]

    const result = await documentApi.batchVectorizeFolder(folder.id, batchVectorizeMode.value)

    message.success(result.message || '批量向量化任务已启动')

    // 重置模式选择
    batchVectorizeMode.value = 'incremental'

    // 10秒后移除loading状态（任务已在后台进行）
    setTimeout(() => {
      batchVectorizingFolders.value = batchVectorizingFolders.value.filter(id => id !== folder.id)
    }, 10000)

    // 定时刷新文档列表
    const refreshInterval = setInterval(async () => {
      await loadDocuments()
    }, 5000) // 每5秒刷新一次

    // 30秒后停止自动刷新
    setTimeout(() => {
      clearInterval(refreshInterval)
    }, 30000)
  } catch (error) {
    message.error('批量向量化失败：' + (error as Error).message)
    batchVectorizingFolders.value = batchVectorizingFolders.value.filter(id => id !== folder.id)
  }
}

onMounted(() => {
  loadFolders()
})
</script>

<style scoped>
.knowledge-view {
  height: 100%;
}

.knowledge-view :deep(.n-list-item) {
  position: relative;
  transition: all 0.2s;
}

.is-active {
  background-color: var(--n-color-modal) !important;
  border-radius: 8px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--n-color-target);
  border-radius: 8px 0 0 8px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.document-item {
  padding: 8px 12px;
  background-color: var(--n-card-color);
  border: 1px solid var(--n-border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.document-item:hover {
  background-color: var(--n-color-hover);
  border-color: var(--n-border-color);
}

.pdf-viewer-container {
  width: 100%;
  height: calc(100vh - 200px);
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}

.markdown-content {
  padding: 16px;
  line-height: 1.8;
}

.document-item {
  position: relative;
  transition: all 0.2s;
}

.delete-btn {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.delete-btn:hover {
  opacity: 1 !important;
}

.document-item:hover .delete-btn {
  opacity: 0.8;
}

/* 批量向量化模式选择样式 */
.mode-option {
  padding: 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-option:hover {
  background-color: var(--n-color-hover);
  border-color: var(--n-color-target);
}

.mode-option.is-selected {
  background-color: var(--n-color-modal);
  border-color: var(--n-color-target);
  border-width: 2px;
}

</style>
