<template>
  <div class="document-list-item" @click="$emit('click')">
    <n-space align="center" style="width: 100%">
      <n-icon size="32" :component="FileIcon" />

      <div style="flex: 1; min-width: 0">
        <n-space vertical size="small" style="width: 100%">
          <n-space justify="space-between" align="center">
            <n-text strong>{{ document.title }}</n-text>
            <n-tag size="small" :type="getStatusType()" :bordered="false">
              {{ getStatusText() }}
            </n-tag>
          </n-space>

          <n-text depth="3" style="font-size: 12px">
            {{ document.fileName }} · {{ formatFileSize(document.fileSize) }}
          </n-text>

          <n-space size="small">
            <n-tag
              v-for="tag in document.tags"
              :key="tag"
              size="small"
              :bordered="false"
              type="info"
            >
              {{ tag }}
            </n-tag>
          </n-space>
        </n-space>
      </div>

      <n-button-group>
        <n-button v-if="!document.parsed" type="primary" size="small" @click.stop="$emit('parse')">
          解析
        </n-button>
        <n-button v-else size="small" @click.stop="handlePreview">
          预览
        </n-button>
      </n-button-group>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import type { Document } from '@/types/document'
import { DocumentOutline as FileIcon } from '@vicons/ionicons5'

interface Props {
  document: Document
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: []
  parse: []
}>()

function getStatusType() {
  switch (props.document.parseStatus) {
    case 'success':
      return 'success'
    case 'error':
      return 'error'
    case 'parsing':
      return 'warning'
    default:
      return 'default'
  }
}

function getStatusText() {
  switch (props.document.parseStatus) {
    case 'success':
      return '已解析'
    case 'error':
      return '解析失败'
    case 'parsing':
      return '解析中...'
    case 'pending':
    default:
      return '待解析'
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handlePreview() {
  emit('click')
}
</script>

<style scoped>
.document-list-item {
  cursor: pointer;
  width: 100%;
  padding: 8px 0;
}

.document-list-item:hover {
  background-color: var(--n-color-modal);
  border-radius: 8px;
  padding: 8px 12px;
  margin: 0 -12px;
}
</style>
