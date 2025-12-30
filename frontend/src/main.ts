import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Naive UI 组件导入
import {
  create,
  // 基础组件
  NButton,
  NCard,
  NConfigProvider,
  NMessageProvider,
  // 布局组件
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NBreadcrumb,
  NBreadcrumbItem,
  NSpace,
  NDivider,
  // 数据展示
  NIcon,
  NSpin,
  NEmpty,
  NList,
  NListItem,
  NTag,
  NText,
  NH1,
  NH2,
  NH3,
  NP,
  NTooltip,
  NAlert,
  // 表单组件
  NInput,
  NSelect,
  NButtonGroup,
  NUpload,
  NUploadDragger,
  NProgress,
  NModal,
  NDropdown,
  NForm,
  NFormItem,
  NDrawer,
  NTabs,
  NTabPane,
  NDescriptions,
  NDescriptionsItem,
  NSwitch,
} from 'naive-ui'

const naive = create({
  components: [
    NButton,
    NCard,
    NConfigProvider,
    NMessageProvider,
    NLayout,
    NLayoutSider,
    NLayoutHeader,
    NLayoutContent,
    NMenu,
    NBreadcrumb,
    NBreadcrumbItem,
    NSpace,
    NDivider,
    NIcon,
    NSpin,
    NEmpty,
    NList,
    NListItem,
    NTag,
    NText,
    NH1,
    NH2,
    NH3,
    NP,
    NTooltip,
    NAlert,
    NInput,
    NSelect,
    NButtonGroup,
    NUpload,
    NUploadDragger,
    NProgress,
    NModal,
    NDropdown,
    NForm,
    NFormItem,
    NDrawer,
    NTabs,
    NTabPane,
    NDescriptions,
    NDescriptionsItem,
    NSwitch,
  ],
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

app.mount('#app')
