<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import type { GlobalThemeOverrides } from 'naive-ui'

// Gemini 风格主题配置
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#1a73e8',
    primaryColorHover: '#1557b0',
    primaryColorPressed: '#0d47a1',
    borderRadius: '12px',
  },
}
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
}
</style>
