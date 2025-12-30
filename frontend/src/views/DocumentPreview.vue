<template>
  <div class="document-preview">
    <!-- 顶部工具栏 -->
    <n-layout-header bordered style="height: 60px; padding: 0 24px; display: flex; align-items: center; justify-content: space-between;">
      <n-space align="center">
        <n-button text @click="goBack">
          <template #icon>
            <n-icon :component="ArrowBackIcon" />
          </template>
          返回
        </n-button>
        <n-divider vertical />
        <n-text strong>{{ document?.title || '加载中...' }}</n-text>
        <n-tag v-if="document" size="small" :type="document.parsed ? 'success' : 'warning'">
          {{ document.parsed ? '已解析' : '待解析' }}
        </n-tag>
      </n-space>

      <n-space>
        <n-button @click="handleParse" :loading="isParsing" :disabled="!document || document.parsed">
          <template #icon>
            <n-icon :component="RefreshIcon" />
          </template>
          解析文档
        </n-button>
        <n-button v-if="!isPreviewMode" type="primary" @click="handleSave" :loading="isSaving">
          <template #icon>
            <n-icon :component="SaveIcon" />
          </template>
          保存修改
        </n-button>
      </n-space>
    </n-layout-header>

    <!-- 主内容区：分屏显示 -->
    <n-layout-content style="height: calc(100vh - 60px);">
      <div class="split-view">
        <!-- 左侧：PDF 预览 -->
        <div class="left-panel">
          <div class="panel-header">
            <n-text strong>原文档 (PDF)</n-text>
          </div>
          <div class="pdf-container">
            <PDFViewer v-if="document" :document-id="document.id" />
            <n-empty v-else description="文档加载中..." />
          </div>
        </div>

        <!-- 右侧：Markdown 编辑器 -->
        <div class="right-panel">
          <div class="panel-header">
            <n-space align="center" justify="space-between" style="width: 100%">
              <n-text strong>解析内容 (Markdown)</n-text>
              <n-switch v-model:value="isPreviewMode">
                <template #checked>
                  预览
                </template>
                <template #unchecked>
                  编辑
                </template>
              </n-switch>
            </n-space>
          </div>

          <!-- 编辑模式 -->
          <div v-if="!isPreviewMode" class="editor-container">
            <textarea
              v-model="markdownContent"
              class="markdown-editor"
              spellcheck="false"
              placeholder="文档尚未解析，请点击上方解析文档按钮开始解析..."
            ></textarea>
          </div>

          <!-- 预览模式 -->
          <div v-else class="preview-container">
            <div class="markdown-preview" v-html="renderedMarkdown"></div>
          </div>
        </div>
      </div>
    </n-layout-content>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
// 导入代码高亮样式
import 'highlight.js/styles/github-dark.css'
import {
  ArrowBackOutline as ArrowBackIcon,
  RefreshOutline as RefreshIcon,
  SaveOutline as SaveIcon,
} from '@vicons/ionicons5'
import { documentApi } from '@/api/document'
import type { Document } from '@/types/document'
import PDFViewer from '@/components/common/PDFViewer.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 配置 Markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  }
})

const documentId = ref(route.params.id as string)
const document = ref<Document | null>(null)
const markdownContent = ref('')
const isSaving = ref(false)
const isParsing = ref(false)
const isLoading = ref(false)
const isPreviewMode = ref(false)

// 轮询定时器
let pollingInterval: number | null = null

// 自定义图片渲染规则（在 computed 之前定义）
const defaultImageRender = md.renderer.rules.image || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.image = function (tokens, idx, options, env, self) {
  const token = tokens[idx]
  const src = token.attrGet('src')

  // 如果是相对路径（images/xxx.jpg），转换为后端 API 路径
  if (src && src.startsWith('images/')) {
    const imageName = src.replace('images/', '')
    const apiUrl = `/api/documents/${documentId.value}/images/${imageName}`
    token.attrSet('src', apiUrl)
  }

  // 使用默认渲染器
  return defaultImageRender(tokens, idx, options, env, self)
}

// 渲染 Markdown
const renderedMarkdown = computed(() => {
  if (!markdownContent.value) return ''
  try {
    return md.render(markdownContent.value)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return markdownContent.value
  }
})

async function loadDocument() {
  try {
    isLoading.value = true
    const doc = await documentApi.get(documentId.value)
    document.value = doc

    // 确保 markdownContent 被正确赋值
    const content = doc.markdownContent || ''
    markdownContent.value = content
  } catch (error) {
    console.error('加载文档失败:', error)
    message.error('加载文档失败: ' + (error as Error).message)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.back()
}

async function handleSave() {
  if (!document.value) return

  try {
    isSaving.value = true
    await documentApi.updateContent(document.value.id, markdownContent.value)
    message.success('保存成功')

    // 更新本地文档状态
    document.value.markdownContent = markdownContent.value
    document.value.parsed = true
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败: ' + (error as Error).message)
  } finally {
    isSaving.value = false
  }
}

async function handleParse() {
  if (!document.value) return

  // 清除之前的轮询
  if (pollingInterval !== null) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }

  try {
    isParsing.value = true
    message.info('解析任务已启动，正在后台处理，请耐心等待...', {
      duration: 5000
    })

    // 启动解析任务
    await documentApi.parse(document.value.id)

    // 开始轮询解析状态
    pollParseStatus()
  } catch (error) {
    console.error('启动解析任务失败:', error)
    message.error('启动解析任务失败：' + (error as Error).message)
    isParsing.value = false
  }
}

// 轮询解析状态
function pollParseStatus() {
  if (!document.value) return

  const maxAttempts = 300 // 最多轮询10分钟（每2秒一次）
  let attempts = 0
  let consecutiveErrors = 0 // 连续错误次数

  pollingInterval = setInterval(async () => {
    attempts++

    try {
      const status = await documentApi.getParseStatus(document.value.id)

      console.log('解析状态:', status)

      // 重置错误计数
      consecutiveErrors = 0

      // 更新文档状态
      if (document.value) {
        document.value.parseStatus = status.status
        document.value.parsed = status.parsed
      }

      if (status.status === 'success' || status.parsed) {
        stopPolling()
        message.success('解析成功！')
        await loadDocument()
      } else if (status.status === 'error') {
        stopPolling()
        message.error('解析失败，请查看日志')
      } else if (attempts >= maxAttempts) {
        stopPolling()
        message.warning('解析时间较长，请稍后手动刷新查看结果')
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`获取解析状态失败 (第${consecutiveErrors}次):`, error)

      // 连续失败5次才停止轮询（容错处理）
      if (consecutiveErrors >= 5) {
        stopPolling()
        message.error('获取解析状态失败，请稍后重试')
      }
      // 否则继续轮询
    }
  }, 2000) // 每2秒轮询一次
}

// 停止轮询
function stopPolling() {
  if (pollingInterval !== null) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  isParsing.value = false
}

onMounted(() => {
  loadDocument()
})

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    documentId.value = newId as string
    loadDocument()
  }
})
</script>

<style scoped>
.document-preview {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.split-view {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.left-panel,
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.left-panel {
  border-right: 1px solid var(--n-border-color);
  background-color: #525659;
}

.right-panel {
  background-color: #fff;
}

.panel-header {
  padding: 10px 16px;
  border-bottom: 1px solid var(--n-border-color);
  background-color: var(--n-color-modal);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pdf-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.editor-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.preview-container {
  flex: 1;
  overflow: auto;
  position: relative;
  padding: 20px;
}

.markdown-editor {
  width: 100%;
  height: 100%;
  border: none;
  resize: none;
  padding: 20px;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.8;
  background-color: var(--n-color);
  color: var(--n-text-color);
  outline: none;
  box-sizing: border-box;
}

.markdown-preview {
  width: 100%;
  font-size: 15px;
  line-height: 1.8;
  color: var(--n-text-color);
}

.markdown-preview h1,
.markdown-preview h2,
.markdown-preview h3,
.markdown-preview h4,
.markdown-preview h5,
.markdown-preview h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-preview h1 {
  font-size: 2em;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 8px;
}

.markdown-preview h2 {
  font-size: 1.5em;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 8px;
}

.markdown-preview p {
  margin-bottom: 16px;
}

.markdown-preview code {
  background-color: var(--n-code-color);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 0.9em;
}

.markdown-preview pre {
  background-color: var(--n-code-color);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 16px;
}

.markdown-preview pre code {
  background-color: transparent;
  padding: 0;
}

.markdown-preview ul,
.markdown-preview ol {
  padding-left: 2em;
  margin-bottom: 16px;
}

.markdown-preview li {
  margin-bottom: 4px;
}

.markdown-preview img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 16px 0;
}

.markdown-preview table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.markdown-preview table th,
.markdown-preview table td {
  border: 1px solid var(--n-border-color);
  padding: 8px 12px;
}

.markdown-preview table th {
  background-color: var(--n-th-color);
  font-weight: 600;
}

.markdown-preview blockquote {
  border-left: 4px solid var(--n-border-color);
  padding-left: 16px;
  margin: 16px 0;
  color: var(--n-text-color3);
}

.markdown-editor:focus {
  outline: none;
}

.markdown-editor::placeholder {
  color: #999;
}
</style>
