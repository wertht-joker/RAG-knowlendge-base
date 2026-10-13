<template>
  <div class="page">
    <div class="page-header">
      <h3>📄 文档管理</h3>
      <div style="display:flex;gap:12px">
        <el-input v-model="keyword" placeholder="搜索文档名称" style="width:240px" clearable @input="loadDocuments" />
        <el-upload :show-file-list="false" :http-request="handleUpload" accept=".pdf,.docx,.xlsx,.md,.txt">
          <el-button type="primary">上传文档</el-button>
        </el-upload>
      </div>
    </div>

    <el-table :data="documents" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="文档名称" />
      <el-table-column prop="type" label="格式" width="80" />
      <el-table-column prop="chunk_count" label="切分块数" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'done' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
            {{ statusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" text @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api'

const documents = ref([])
const loading = ref(false)
const keyword = ref('')

async function loadDocuments() {
  loading.value = true
  try {
    documents.value = await request.get('/documents', { params: { keyword: keyword.value } })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function handleUpload(options) {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const data = await request.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success(`上传成功，切分为 ${data.chunk_count} 块`)
    loadDocuments()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除文档「${row.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/documents/${row.id}`)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function statusText(s) {
  return { done: '已完成', processing: '处理中', failed: '失败' }[s] || s
}

function formatTime(t) {
  return t ? String(t).replace('T', ' ').slice(0, 19) : ''
}

onMounted(loadDocuments)
</script>

<style scoped>
.page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
