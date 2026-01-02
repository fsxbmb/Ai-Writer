import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import HomeView from '@/views/HomeView.vue'
import KnowledgeView from '@/views/KnowledgeView.vue'
import DocumentPreview from '@/views/DocumentPreview.vue'

const routes: RouteRecordRaw[] = [
  // 首页 - 独立显示，不带侧边栏
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: { title: '首页' },
  },
  // 其他页面 - 使用 MainLayout（带侧边栏）
  {
    path: '/',
    component: MainLayout,
    children: [
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
