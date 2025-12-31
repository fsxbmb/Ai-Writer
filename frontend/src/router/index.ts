import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import KnowledgeView from '@/views/KnowledgeView.vue'
import DocumentPreview from '@/views/DocumentPreview.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        redirect: '/knowledge',
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: KnowledgeView,
        meta: { title: '知识库管理', icon: 'database' },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/ChatView.vue'),
        meta: { title: '知识问答', icon: 'chat' },
      },
      {
        path: 'chat/:id',
        name: 'ChatDocument',
        component: () => import('@/views/ChatView.vue'),
        meta: { title: '知识问答', icon: 'chat' },
      },
      {
        path: 'document',
        name: 'Document',
        component: () => import('@/views/DocumentView.vue'),
        meta: { title: '文档生成', icon: 'document' },
      },
    ],
  },
  {
    path: '/document/:id',
    name: 'DocumentPreview',
    component: DocumentPreview,
    meta: { title: '文档预览' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
