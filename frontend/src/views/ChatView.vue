<template>
  <div class="chat-layout">
    <!-- 左侧：会话列表 -->
    <div class="session-panel">
      <div class="session-header">
        <el-button type="primary" size="small" style="width:100%" @click="newChat">+ 新对话</el-button>
      </div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === sessionId }"
          @click="loadSession(s.id)"
        >
          <div class="session-title">{{ s.title }}</div>
          <div class="session-time">{{ formatTime(s.created_at) }}</div>
          <el-button class="session-del" size="small" text type="danger" @click.stop="removeSession(s.id)">🗑</el-button>
        </div>
        <div v-if="sessions.length === 0" class="no-session">暂无历史对话</div>
      </div>
    </div>

    <!-- 右侧：聊天区 -->
    <div class="chat-container">
      <div class="chat-header">
        <span>💬 智能问答</span>
      </div>

      <div class="chat-body" ref="chatBody">
        <div v-if="messages.length === 0" class="empty-tip">
          <div class="empty-icon">🤖</div>
          <div>你好，我是企业客服助手，可以问我产品、售后、政策等问题</div>
          <div class="suggest">
            <el-tag v-for="q in suggestions" :key="q" class="suggest-tag" @click="askSuggest(q)">{{ q }}</el-tag>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" class="msg-row" :class="msg.role">
          <!-- Agent 中间步骤：模型自主调用了哪些工具 -->
          <div v-if="msg.role === 'assistant' && msg.steps && msg.steps.length" class="steps">
            <div v-for="(s, k) in msg.steps" :key="k" class="step-pill">{{ s }}</div>
          </div>

          <div class="bubble">{{ msg.content }}<span v-if="msg.streaming" class="cursor">▌</span></div>

          <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length" class="sources">
            <el-collapse>
              <el-collapse-item :title="`📎 引用来源（${msg.sources.length} 条）`">
                <div v-for="(s, j) in msg.sources" :key="j" class="source-item">
                  <div class="source-doc">📄 {{ s.doc_name }} · 相关度 {{ s.score }}</div>
                  <div class="source-text">{{ s.text }}</div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <div v-if="msg.role === 'assistant' && msg.messageId" class="feedback">
            <el-button size="small" text @click="feedback(msg.messageId, 'up')">👍</el-button>
            <el-button size="small" text @click="feedback(msg.messageId, 'down')">👎</el-button>
          </div>
        </div>
      </div>

      <div class="chat-footer">
        <el-input
          v-model="input"
          placeholder="输入问题，回车发送"
          @keyup.enter="send"
          :disabled="loading"
        />
        <el-button type="primary" @click="send" :loading="loading">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request, { TOKEN_KEY } from '../api'

const messages = ref([])
const sessions = ref([])
const input = ref('')
const loading = ref(false)
const sessionId = ref(null)
const chatBody = ref(null)

const suggestions = ['空气净化器怎么换滤网？', '退货多久能退款？', '查一下订单 DD20260901001 到哪了？', '会员积分怎么用？']

async function loadSessions() {
  try {
    sessions.value = await request.get('/sessions')
  } catch (e) {}
}

function newChat() {
  messages.value = []
  sessionId.value = null
}

function askSuggest(q) {
  input.value = q
  send()
}

// 加载某个历史会话的消息
async function loadSession(id) {
  sessionId.value = id
  try {
    const msgs = await request.get(`/sessions/${id}/messages`)
    messages.value = msgs.map((m) => ({
      role: m.role,
      content: m.content,
      sources: [],
      steps: [],
      messageId: null,
    }))
    scrollBottom()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

// 删除会话
async function removeSession(id) {
  try {
    await request.delete(`/sessions/${id}`)
    ElMessage.success('已删除')
    if (sessionId.value === id) {
      newChat()
    }
    loadSessions()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function send() {
  const q = input.value.trim()
  if (!q || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: q })
  const aiMsg = { role: 'assistant', content: '', sources: [], steps: [], messageId: null, streaming: true }
  messages.value.push(aiMsg)
  loading.value = true
  scrollBottom()

  try {
    const token = localStorage.getItem(TOKEN_KEY)
    const resp = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify({ question: q, session_id: sessionId.value }),
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const line = part.trim()
        if (line.startsWith('data:')) {
          try { handleEvent(JSON.parse(line.slice(5).trim()), aiMsg) } catch (e) {}
        }
      }
    }
  } catch (e) {
    ElMessage.error(e.message)
    aiMsg.content = aiMsg.content || '请求失败：' + e.message
  } finally {
    loading.value = false
    aiMsg.streaming = false
    loadSessions()
    scrollBottom()
  }
}

function handleEvent(event, aiMsg) {
  if (event.type === 'meta') {
    aiMsg.sources = event.sources
    sessionId.value = event.session_id
    if (event.message_id) aiMsg.messageId = event.message_id
  } else if (event.type === 'step') {
    // Agent 调用工具的中间步骤，实时追加展示
    aiMsg.steps.push(event.label)
    scrollBottom()
  } else if (event.type === 'delta') {
    aiMsg.content += event.content
    scrollBottom()
  } else if (event.type === 'done') {
    aiMsg.messageId = event.message_id
  }
}

async function feedback(messageId, type) {
  try {
    await request.post('/feedback', { message_id: messageId, type })
    ElMessage.success('感谢反馈')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function formatTime(t) {
  return t ? String(t).replace('T', ' ').slice(5, 16) : ''
}

function scrollBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}

onMounted(loadSessions)
</script>

<style scoped>
.chat-layout { display: flex; height: 100vh; }
.session-panel { width: 220px; background: #fff; border-right: 1px solid #eee; display: flex; flex-direction: column; }
.session-header { padding: 12px; border-bottom: 1px solid #eee; }
.session-list { flex: 1; overflow-y: auto; }
.session-item { padding: 12px 16px; cursor: pointer; border-bottom: 1px solid #f5f5f5; position: relative; }
.session-del { position: absolute; right: 6px; top: 8px; opacity: 0; }
.session-item:hover .session-del { opacity: 1; }
.session-item:hover { background: #f5f7fa; }
.session-item.active { background: #ecf5ff; border-left: 3px solid #409eff; }
.session-title { font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-time { font-size: 11px; color: #999; margin-top: 4px; }
.no-session { text-align: center; color: #ccc; font-size: 13px; padding: 30px 0; }
.chat-container { flex: 1; display: flex; flex-direction: column; background: #fff; }
.chat-header { padding: 16px 20px; border-bottom: 1px solid #eee; font-weight: bold; }
.chat-body { flex: 1; overflow-y: auto; padding: 20px; }
.empty-tip { text-align: center; color: #999; margin-top: 100px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.suggest { margin-top: 20px; }
.suggest-tag { margin: 0 6px; cursor: pointer; }
.msg-row { margin-bottom: 20px; display: flex; flex-direction: column; }
.msg-row.user { align-items: flex-end; }
.msg-row.assistant { align-items: flex-start; }
.bubble { max-width: 70%; padding: 12px 16px; border-radius: 10px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.user .bubble { background: #409eff; color: #fff; border-top-right-radius: 2px; }
.assistant .bubble { background: #f4f4f5; color: #333; border-top-left-radius: 2px; }
.cursor { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.steps { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; max-width: 70%; }
.step-pill { align-self: flex-start; background: #f0f2f5; color: #666; font-size: 12px; padding: 4px 10px; border-radius: 10px; }
.sources { width: 70%; margin-top: 8px; }
.source-item { padding: 8px 0; border-bottom: 1px dashed #eee; }
.source-doc { font-size: 13px; color: #409eff; margin-bottom: 4px; }
.source-text { font-size: 12px; color: #999; line-height: 1.5; }
.feedback { margin-top: 4px; }
.chat-footer { display: flex; gap: 12px; padding: 16px 20px; border-top: 1px solid #eee; }
</style>
