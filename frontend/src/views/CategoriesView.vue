<template>
  <div class="page">
    <div class="page-header">
      <h3>🗂️ 分类管理</h3>
      <el-button type="primary" @click="openAdd">+ 新增分类</el-button>
    </div>

    <el-table :data="categories" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="分类名称" />
      <el-table-column prop="parent_id" label="层级" width="100">
        <template #default="{ row }">
          <el-tag :type="row.parent_id === 0 ? 'primary' : 'info'">
            {{ row.parent_id === 0 ? '一级分类' : '二级分类' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort" label="排序" width="80" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新增分类'" width="400px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="分类名称" />
        </el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="form.parent_id" placeholder="一级分类">
            <el-option label="（一级分类）" :value="0" />
            <el-option v-for="c in topCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api'

const categories = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ name: '', parent_id: 0, sort: 0 })

const topCategories = computed(() => categories.value.filter((c) => c.parent_id === 0))

async function loadCategories() {
  loading.value = true
  try {
    categories.value = await request.get('/categories')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openAdd() {
  editing.value = null
  form.value = { name: '', parent_id: 0, sort: 0 }
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  form.value = { name: row.name, parent_id: row.parent_id, sort: row.sort }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name.trim()) return ElMessage.warning('请输入分类名称')
  try {
    if (editing.value) {
      await request.put(`/categories/${editing.value.id}`, form.value)
    } else {
      await request.post('/categories', form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除分类「${row.name}」？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/categories/${row.id}`)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
</style>
