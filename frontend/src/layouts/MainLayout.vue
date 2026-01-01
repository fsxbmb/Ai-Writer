<template>
  <n-layout has-sider style="height: 100vh">
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      show-trigger
      :collapsed-width="64"
      :width="187"
      :collapsed="appStore.sidebarCollapsed"
      @collapse="appStore.setSidebarCollapsed(true)"
      @expand="appStore.setSidebarCollapsed(false)"
    >
      <div class="logo">
        <h2 v-if="!appStore.sidebarCollapsed">军文智写助手</h2>
        <h2 v-else>AI</h2>
      </div>

      <n-menu
        :collapsed="appStore.sidebarCollapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="currentRoute"
        @update:value="handleMenuSelect"
      />

      <!-- 主题切换按钮 -->
      <div class="theme-toggle">
        <n-tooltip placement="right" :disabled="!appStore.sidebarCollapsed">
          <template #trigger>
            <n-button
              text
              size="large"
              :style="{ width: appStore.sidebarCollapsed ? '100%' : 'auto' }"
              @click="appStore.toggleTheme"
            >
              <template #icon>
                <n-icon>
                  <SunnyOutline v-if="appStore.isDark" />
                  <MoonOutline v-else />
                </n-icon>
              </template>
              <span v-if="!appStore.sidebarCollapsed">
                {{ appStore.isDark ? '浅色' : '深色' }}
              </span>
            </n-button>
          </template>
          切换主题
        </n-tooltip>
      </div>
    </n-layout-sider>

    <!-- 主内容区 -->
    <n-layout style="height: 100vh; overflow: hidden;">
      <n-layout-header bordered style="height: 60px; padding: 0 24px; display: flex; align-items: center; flex-shrink: 0;">
        <n-space align="center">
          <n-breadcrumb>
            <n-breadcrumb-item>{{ currentRouteMeta?.title || '首页' }}</n-breadcrumb-item>
          </n-breadcrumb>
        </n-space>
      </n-layout-header>

      <n-layout-content style="padding: 24px; overflow: hidden;">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h, Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  FolderOpenOutline as FolderIcon,
  ChatbubbleEllipsesOutline as ChatIcon,
  DocumentTextOutline as DocIcon,
  SunnyOutline,
  MoonOutline,
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

const currentRoute = computed(() => route.name as string)
const currentRouteMeta = computed(() => route.meta as { title?: string; icon?: string })

const renderIcon = (icon: Component) => {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions: MenuOption[] = [
  {
    label: '知识库管理',
    key: 'Knowledge',
    icon: renderIcon(FolderIcon),
  },
  {
    label: '知识问答',
    key: 'Chat',
    icon: renderIcon(ChatIcon),
  },
  {
    label: '文档生成',
    key: 'Document',
    icon: renderIcon(DocIcon),
  },
]

function handleMenuSelect(key: string) {
  router.push({ name: key })
}
</script>

<style scoped>
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--n-border-color);
  margin-bottom: 8px;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--n-text-color);
}

.theme-toggle {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 0 8px;
}
</style>
