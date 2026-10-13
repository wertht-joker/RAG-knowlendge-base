<template>
  <el-container class="layout">
    <el-aside width="200px" class="aside">
      <div class="logo">🤖 客服知识库</div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/">💬 智能问答</el-menu-item>
        <el-menu-item index="/documents">📄 文档管理</el-menu-item>
        <el-menu-item index="/categories">🗂️ 分类管理</el-menu-item>
      </el-menu>
      <div class="user-box">
        <span class="username">👤 {{ username }}</span>
        <el-button text size="small" @click="logout">退出</el-button>
      </div>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { TOKEN_KEY } from './api'

const route = useRoute()
const activeMenu = computed(() => route.path)

const username = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('kb_user') || '{}')
    return u.username || '未登录'
  } catch {
    return '未登录'
  }
})

function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem('kb_user')
  window.location.href = '/login'
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f6fa; }
.layout { height: 100vh; }
.aside { background: #fff; border-right: 1px solid #eee; display: flex; flex-direction: column; }
.logo { font-size: 18px; font-weight: bold; color: #409eff; padding: 20px 16px; }
.user-box { margin-top: auto; padding: 16px; border-top: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; }
.username { font-size: 13px; color: #666; }
.main { padding: 0; background: #f5f6fa; }
</style>
