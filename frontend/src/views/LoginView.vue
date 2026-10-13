<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">🤖 客服知识库</div>
      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>
      <el-form>
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" show-password @keyup.enter="submit" />
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="loading" @click="submit">
          {{ tab === 'login' ? '登录' : '注册' }}
        </el-button>
      </el-form>
      <div class="login-tip">
        默认管理员：admin / admin123
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request, { TOKEN_KEY } from '../api'

const tab = ref('login')
const loading = ref(false)
const form = ref({ username: '', password: '' })

async function submit() {
  if (!form.value.username || !form.value.password) {
    return ElMessage.warning('请输入用户名和密码')
  }
  loading.value = true
  try {
    const path = tab.value === 'login' ? '/auth/login' : '/auth/register'
    const data = await request.post(path, form.value)
    if (tab.value === 'login') {
      localStorage.setItem(TOKEN_KEY, data.token)
      localStorage.setItem('kb_user', JSON.stringify(data.user))
      ElMessage.success('登录成功')
      window.location.href = '/'
    } else {
      ElMessage.success('注册成功，请登录')
      tab.value = 'login'
      form.value.password = ''
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-card { width: 360px; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 8px 30px rgba(0,0,0,.15); }
.login-logo { text-align: center; font-size: 20px; font-weight: bold; color: #409eff; margin-bottom: 16px; }
.login-tip { text-align: center; color: #999; font-size: 12px; margin-top: 16px; }
</style>
