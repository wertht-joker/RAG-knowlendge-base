import axios from 'axios'

const request = axios.create({ baseURL: '/api/v1' })

export const TOKEN_KEY = 'kb_token'

// 请求拦截器：自动带 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
})

// 响应拦截器：统一解包 + 处理 401/403
request.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data.code === 200) return data.data
    if (data.code === 401) {
      localStorage.removeItem(TOKEN_KEY)
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  (err) => {
    // HTTP 401/403（鉴权依赖抛出的）
    if (err.response && (err.response.status === 401 || err.response.status === 403)) {
      localStorage.removeItem(TOKEN_KEY)
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  },
)

export default request
