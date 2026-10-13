import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import DocumentsView from '../views/DocumentsView.vue'
import CategoriesView from '../views/CategoriesView.vue'
import LoginView from '../views/LoginView.vue'
import { TOKEN_KEY } from '../api'

const routes = [
  { path: '/login', name: 'login', component: LoginView },
  { path: '/', name: 'chat', component: ChatView, meta: { title: '智能问答', requiresAuth: true } },
  { path: '/documents', name: 'documents', component: DocumentsView, meta: { title: '文档管理', requiresAuth: true } },
  { path: '/categories', name: 'categories', component: CategoriesView, meta: { title: '分类管理', requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 登录守卫：需要登录的页面，未登录跳转登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
