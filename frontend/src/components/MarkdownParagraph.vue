<template>
  <div class="markdown-paragraph-container">
    <!-- 预览模式（Markdown 渲染） - 默认显示 -->
    <div
      v-if="!isEditMode"
      class="markdown-preview"
      v-html="renderedContent"
      :style="previewStyle"
      @click="handleClickPreview"
    ></div>

    <!-- 编辑模式 -->
    <div
      v-else
      ref="editRef"
      contenteditable="true"
      @blur="handleBlur"
      @keydown="handleKeydown"
      class="markdown-editor"
      :style="editorStyle"
    >{{ content }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps<{
  content: string
  isEditing?: boolean
  minHeight?: string
  backgroundColor?: string
}>()

const emit = defineEmits<{
  blur: [event: FocusEvent]
}>()

const md = new MarkdownIt({
  html: true,  // 改为true，允许KaTeX生成的HTML
  linkify: true,
  typographer: true,
  breaks: true,
})

const editRef = ref<HTMLDivElement>()
const isEditMode = ref(false) // 内部编辑模式状态，默认 false（预览模式）

// 处理点击预览
const handleClickPreview = () => {
  // 只有当前版本可编辑
  if (props.isEditing) {
    isEditMode.value = true
  }
}

// 处理失去焦点
const handleBlur = (event: FocusEvent) => {
  isEditMode.value = false
  emit('blur', event)
}

// 渲染数学公式（使用占位符避免被markdown-it破坏）
const renderedContent = computed(() => {
  if (!props.content) return ''

  const formulas: { placeholder: string; latex: string; type: 'inline' | 'block' }[] = []
  let counter = 0
  let content = props.content

  // 调试：输出原始内容
  if (props.content.includes('$')) {
    console.log('[MarkdownParagraph] 处理包含公式的内容:', props.content.substring(0, 100))
  }

  // 先提取块级公式并用占位符替换（使用不会被markdown-it处理的占位符）
  content = content.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    const placeholder = `MATHBLOCK${counter}PLACEHOLDER`
    formulas.push({ placeholder, latex: formula.trim(), type: 'block' })
    console.log(`[MarkdownParagraph] 提取块级公式 ${counter}:`, formula.trim())
    counter++
    return placeholder
  })

  // 再提取行内公式并用占位符替换
  content = content.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
    const placeholder = `MATHINLINE${counter}PLACEHOLDER`
    formulas.push({ placeholder, latex: formula.trim(), type: 'inline' })
    console.log(`[MarkdownParagraph] 提取行内公式 ${counter}:`, formula.trim())
    counter++
    return placeholder
  })

  console.log('[MarkdownParagraph] 共提取公式:', formulas.length, '个')

  // 先渲染Markdown
  let rendered = md.render(content)
  console.log('[MarkdownParagraph] Markdown渲染后包含占位符:', rendered.includes('MATH'))

  // 最后替换占位符为KaTeX渲染的HTML
  formulas.forEach(({ placeholder, latex, type }) => {
    try {
      const html = katex.renderToString(latex, {
        displayMode: type === 'block',
        throwOnError: false,
      })
      console.log(`[MarkdownParagraph] 替换占位符 ${placeholder} 为 KaTeX HTML`)
      rendered = rendered.replace(placeholder, html)
    } catch (e) {
      console.error('[MarkdownParagraph] 公式渲染错误:', latex, e)
      const errorHtml = type === 'block'
        ? `<div class="math-error">公式错误: ${latex}</div>`
        : `<span class="math-error">公式错误</span>`
      rendered = rendered.replace(placeholder, errorHtml)
    }
  })

  console.log('[MarkdownParagraph] 最终结果包含 katex 类:', rendered.includes('katex'))
  return rendered
})

const editorStyle = computed(() => ({
  padding: '12px',
  border: '1px solid var(--n-border-color)',
  borderRadius: '4px',
  minHeight: props.minHeight || '60px',
  whiteSpace: 'pre-wrap',
  lineHeight: '1.8',
  backgroundColor: props.backgroundColor || 'var(--n-color)',
  cursor: 'text',
  fontFamily: 'inherit',
  fontSize: 'inherit',
}))

const previewStyle = computed(() => ({
  padding: '12px',
  border: '1px solid var(--n-border-color)',
  borderRadius: '4px',
  minHeight: props.minHeight || '60px',
  lineHeight: '1.8',
  backgroundColor: props.backgroundColor || 'var(--n-color-modal)',
  opacity: '0.95',
  fontFamily: 'inherit',
  fontSize: 'inherit',
  cursor: props.isEditing ? 'text' : 'default',
}))

const handleKeydown = (event: KeyboardEvent) => {
  // 阻止换行时创建 div，改用 br
  if (event.key === 'Enter') {
    event.preventDefault()
    const selection = window.getSelection()
    if (selection && selection.rangeCount > 0) {
      const range = selection.getRangeAt(0)
      const br = document.createElement('br')
      range.insertNode(br)
      range.setStartAfter(br)
      range.collapse(true)
      selection.removeAllRanges()
      selection.addRange(range)
    }
  }
}

// 当进入编辑模式时，聚焦编辑器
watch(isEditMode, async (editing) => {
  if (editing) {
    await nextTick()
    if (editRef.value) {
      editRef.value.focus()
      // 将光标移到末尾
      const range = document.createRange()
      const selection = window.getSelection()
      if (selection && editRef.value) {
        range.selectNodeContents(editRef.value)
        range.collapse(false)
        selection.removeAllRanges()
        selection.addRange(range)
      }
    }
  }
})
</script>

<style scoped>
.markdown-paragraph-container {
  width: 100%;
}

.markdown-editor,
.markdown-preview {
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* Markdown 预览样式 */
.markdown-preview :deep(h1),
.markdown-preview :deep(h2),
.markdown-preview :deep(h3),
.markdown-preview :deep(h4) {
  font-weight: bold;
  margin: 0.6em 0 0.3em 0;
}

.markdown-preview :deep(h1) {
  font-size: 1.6em;
  border-bottom: 2px solid var(--n-border-color);
  padding-bottom: 0.3em;
}

.markdown-preview :deep(h2) {
  font-size: 1.4em;
  border-bottom: 1px solid var(--n-border-color);
  padding-bottom: 0.3em;
}

.markdown-preview :deep(h3) {
  font-size: 1.2em;
}

.markdown-preview :deep(p) {
  margin: 0.5em 0;
}

.markdown-preview :deep(strong) {
  font-weight: bold;
}

.markdown-preview :deep(em) {
  font-style: italic;
}

.markdown-preview :deep(code) {
  background-color: var(--n-code-color);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-preview :deep(pre) {
  background-color: var(--n-code-color);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.8em 0;
}

.markdown-preview :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-preview :deep(ul),
.markdown-preview :deep(ol) {
  margin: 0.5em 0;
  padding-left: 2em;
}

.markdown-preview :deep(li) {
  margin: 0.3em 0;
}

.markdown-preview :deep(blockquote) {
  border-left: 4px solid var(--n-primary-color);
  padding-left: 1em;
  margin: 0.8em 0;
  color: var(--n-text-color-2);
}

.markdown-preview :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
}

.markdown-preview :deep(th),
.markdown-preview :deep(td) {
  border: 1px solid var(--n-border-color);
  padding: 8px 12px;
}

.markdown-preview :deep(th) {
  background-color: var(--n-th-color);
  font-weight: bold;
}

.markdown-preview :deep(a) {
  color: var(--n-primary-color);
  text-decoration: none;
}

.markdown-preview :deep(a:hover) {
  text-decoration: underline;
}

/* 数学公式支持 */
.markdown-preview :deep(.math-formula) {
  display: inline-block;
  padding: 8px 12px;
  background-color: var(--n-code-color);
  border-radius: 4px;
  font-family: 'Times New Roman', serif;
  font-style: italic;
}

/* 编辑器中保持纯文本显示 */
.markdown-editor {
  outline: none;
}

.markdown-editor:empty:before {
  content: attr(placeholder);
  color: var(--n-placeholder-color);
}

.markdown-editor:focus {
  border-color: var(--n-primary-color) !important;
}

/* KaTeX 公式样式 */
.markdown-preview :deep(.katex) {
  font-size: 1.1em;
}

.markdown-preview :deep(.katex-display) {
  margin: 1em 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.markdown-preview :deep(.math-error) {
  color: #ff4d4f;
  background-color: #fff2f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
</style>
