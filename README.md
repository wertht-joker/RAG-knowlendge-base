# 企业客服知识库系统（RAG）

基于 **FastAPI + LangChain + Milvus + DeepSeek** 的客服知识库，支持多格式文档入库和**带引用来源的智能问答**。

> 完整需求见 [需求文档.md](./需求文档.md)　|　部署与面试演示见 [部署与演示说明.md](./部署与演示说明.md)

## 功能特性

- **Agent 智能问答（ReAct + Function Calling）**：大模型自主决定调用哪个工具、调几轮，再汇总回答
- 多格式文档入库：PDF / Word / Excel / Markdown，自动解析、切分、向量化
- RAG 智能问答：语义检索 + DeepSeek 生成，答案**附带引用来源**（可溯源到原文）
- 本地 BGE 向量化：离线运行，免 API Key，数据不出本机
- Milvus 企业级向量库

## 技术栈

| 组件 | 选型 |
|---|---|
| 后端框架 | FastAPI |
| RAG 框架 | LangChain（文本切分） |
| 向量库 | Milvus（Docker 部署） |
| 对话模型 | DeepSeek（deepseek-chat） |
| Embedding | 本地 sentence-transformers（BAAI/bge-base-zh-v1.5） |
| 文档解析 | PyMuPDF / python-docx / openpyxl |
| 关系库 | SQLite（SQLAlchemy） |

## 目录结构

```
knowledge-base
├── 需求文档.md
├── docker-compose.yml           # Milvus 编排（etcd + minio + milvus）
├── samples/客服FAQ.md           # 测试文档
└── backend/
    ├── requirements.txt
    ├── .env.example             # 环境变量模板
    └── app/
        ├── main.py              # 主入口
        ├── core/config.py       # 配置管理
        ├── models/              # SQLAlchemy 模型（文档元数据）
        ├── schemas/             # Pydantic 请求/响应模型
        ├── rag/                 # ★ RAG 链路
        │   ├── loader.py        #   文档解析（四格式）
        │   ├── splitter.py      #   文本切分
        │   ├── embedding.py     #   BGE 向量化
        │   ├── vector_store.py  #   Milvus 存储
        │   ├── retriever.py     #   语义检索
        │   └── generator.py     #   DeepSeek 生成
        ├── services/            # 业务编排（文档/问答/会话/反馈/分类）
        └── api/                 # 路由（health/documents/chat/sessions/feedback/categories）
└── frontend/                    # Vue3 前端
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.vue              # 布局（侧边栏导航）
        ├── api/index.js         # axios 封装
        └── views/
            ├── ChatView.vue     # 智能问答（多轮 + 引用 + 反馈）
            ├── DocumentsView.vue # 文档管理
            └── CategoriesView.vue # 分类管理
```

## 环境准备

- Python 3.10+
- Docker Desktop（运行 Milvus）
- DeepSeek API Key（platform.deepseek.com）

## 启动步骤

### 1. 安装依赖

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt  # 首次拉 torch，约 200MB，耐心等
```

### 2. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env`，填入你的 DeepSeek Key（`DEEPSEEK_API_KEY`）。

### 3. 启动 Milvus

```bash
# 回到项目根目录
cd ..
docker compose up -d
docker compose ps      # 确认三个容器 running
```

### 4. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

> 端口被占用时换一个：`--port 8001`

### 5. 启动前端（Vue3）

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173（开发服务器已配置代理，自动转发 /api 到后端）。

> npm 安装慢/失败时，先换镜像：`npm config set registry https://registry.npmmirror.com`

### 6. 验证

- 前端页面：http://localhost:5173
- 健康检查：http://localhost:8000/api/v1/health
- 接口文档：http://localhost:8000/docs

## 接口列表

统一前缀 `/api/v1`，返回结构 `{ code, message, data }`。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /health | 健康检查 |
| POST | /auth/register | 注册（body: `{"username","password"}`） |
| POST | /auth/login | 登录，返回 token |
| POST | /documents/upload | 上传文档（multipart 表单，file 字段） |
| GET | /documents | 文档列表 |
| DELETE | /documents/{id} | 删除文档 |
| POST | /chat | 智能问答（body: `{"question": "...", "session_id": 1}`，带 session_id 续接多轮） |
| POST | /chat/stream | 流式问答（SSE，答案逐字输出） |
| GET | /sessions | 会话列表 |
| GET | /sessions/{id}/messages | 会话消息历史 |
| POST | /feedback | 回答反馈（body: `{"message_id": 1, "type": "up"}`） |
| GET | /feedback/stats | 反馈统计 |
| GET / POST | /categories | 分类列表 / 新增 |
| PUT / DELETE | /categories/{id} | 分类修改 / 删除 |

## 账号与权限

- 默认管理员：**admin / admin123**（首次启动自动创建）
- 管理员：文档管理、分类管理
- 普通用户：注册后登录，可用问答、反馈

> 除注册/登录外，所有接口需在请求头带 `Authorization: Bearer <token>`。

## 使用流程

```
1. 上传文档：POST /documents/upload   →  解析 → 切分 → 向量化 → 入库 Milvus
2. 提问：    POST /chat               →  向量召回 → Rerank 精排 → DeepSeek 生成 → 返回答案 + 引用来源
```

> 前端聊天页默认走 `/chat/stream` 流式接口，答案像 ChatGPT 一样逐字显示。
> 流式事件共 4 种：`step`（Agent 正在调用某工具，前端渲染成灰色步骤标签）、`meta`（会话ID + 引用来源）、`delta`（答案增量）、`done`（结束 + 消息ID）。

### Agent 工具

| 工具 | 作用 | 触发场景 |
|---|---|---|
| `search_knowledge_base` | 检索知识库（向量召回 + Rerank） | 产品、售后、物流、积分、公司介绍等企业知识 |
| `query_order` | 按订单号查状态与物流 | 询问某个具体订单的进度 |

> 演示订单：`DD20260901001`（已发货）、`DD20260912002`（已完成）、`DD20260920003`（待付款），首次启动自动写入。

**测试示例**：

```bash
# 上传测试文档
curl -X POST http://localhost:8000/api/v1/documents/upload -F "file=@../samples/客服FAQ.md"

# 提问
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"退货政策是什么？"}'
```

## 首次运行说明

- **BGE 模型下载**：首次调用向量化会从 HuggingFace 下载模型（约 400MB）。代码已内置 `hf-mirror.com` 镜像加速，无需手动配置。
- **Milvus 镜像拉取**：首次 `docker compose up` 拉取镜像较大，国内可在 Docker Desktop 里配置镜像加速。

## 当前进度

- [x] M1 项目骨架
- [x] M2 文档管理（上传/解析/向量化入库）
- [x] M3 RAG 问答（检索 + 生成 + 引用溯源）
- [x] M4 多轮对话 + 反馈 + 分类
- [x] M5 前端（Vue3）

---

## 面试高频问题（结合本项目）

> 面试官会围绕你简历上的这个 RAG 项目追问，以下问题建议都能用自己的话讲清楚。

**Q1：什么是 RAG？为什么需要它？**
RAG（检索增强生成）＝ 先检索、后生成。传统大模型有「幻觉」问题（会编造不存在的内容），且不知道企业私有知识。RAG 先从企业自己的知识库检索相关片段，再把片段拼进 prompt 让大模型基于真实资料回答，既解决了幻觉，又能回答私有领域问题，还能给出引用来源。

**Q2：这个项目 RAG 的完整流程？**
文档上传 → 解析（PDF/Word/Excel/Markdown）→ 切分 chunk → BGE 向量化 → 存入 Milvus；提问时：向量召回 top20 → Rerank 精排取 top4 → 拼 prompt → DeepSeek 流式生成 → 返回答案 + 引用来源。

**Q3：为什么用 Milvus？和 Chroma/FAISS 有什么区别？**
Milvus 是企业级分布式向量数据库，支持海量向量、高并发、持久化，适合生产环境；Chroma 是轻量嵌入式，适合本地开发/小数据；FAISS 是 Facebook 的向量检索库，不是数据库，需要自己管理存储。选 Milvus 是为了贴近企业级生产架构。

**Q4：Embedding 为什么用本地 BGE 模型？**
① 数据不出内网，保护企业隐私；② 零 API 费用；③ BGE 中文语义效果好。代价是要本地加载模型、首次下载较大。

**Q5：如何解决大模型幻觉？**
三道防线：① system prompt 明确约束「只根据知识内容回答，没有就说未找到」；② 检索不到时直接返回"未找到"，不让模型自由发挥；③ 答案附带引用来源，可溯源。

**Q6：多轮对话怎么处理"那这个呢"这种指代？**
用大模型做 **query 改写**：把历史对话 + 当前问题交给 LLM，改写成完整独立的问题（"那多久退款到账"→"退货退款多久到账"），再用改写后的问题去检索。这是 RAG 多轮场景的关键优化。

**Q7：什么是 Rerank？为什么需要？**
向量检索（双塔模型）速度快但精度一般，召回 top20 后，用 Rerank 模型（CrossEncoder，query 和 passage 一起算相关度）对这 20 条精排，取最相关的 top4。两阶段检索「召回 + 精排」能明显提升答案准确率。

**Q8：流式输出怎么实现？**
后端用 DeepSeek 的 stream 模式，FastAPI 用 `StreamingResponse` 以 SSE（text/event-stream）逐段返回；前端用 `fetch` + `ReadableStream` 边读边渲染，答案像 ChatGPT 一样逐字显示。

**Q9：文档切分（chunk）的策略？**
用 `RecursiveCharacterTextSplitter`，按段落/换行/中文标点（。！？）优先切分，chunk 大小 500 字 + 10% 重叠，避免把一个完整语义切断。

**Q10：为什么用 JWT 鉴权？角色权限怎么设计？**
JWT 无状态、易扩展。登录后生成 token（含用户ID + 角色），请求头带 `Authorization: Bearer <token>`，后端用 FastAPI 依赖 `Depends` 解析校验。角色分管理员（文档/分类管理）和普通用户（问答/反馈）。

**Q11：向量相似度怎么算？**
Embedding 把文本映射成 768 维向量，相似度用余弦相似度（归一化后即内积）。Milvus 里建索引时指定 `metric_type=COSINE`，检索时返回相似度最高的 top-K。

**Q12：文档更新或删除后怎么处理？**
删除文档时同步删除 Milvus 里的向量（按 doc_id 过滤删除）。更新文档则删除旧向量后重新解析入库。元数据存 SQLite，向量存 Milvus，两边通过 doc_id 关联。

---

## 面试高频问题（Agent 部分）

**Q13：什么是 Function Calling（工具调用）？**
大模型本身只会生成文本，不能查数据库、调接口。Function Calling 是让它具备"调用外部能力"的机制：开发者用 JSON Schema 声明有哪些工具、各自要什么参数，随请求一起发给模型；模型判断需要时**不直接回答**，而是返回结构化的 `tool_calls`（工具名 + 参数 JSON）；程序执行后把结果回传，模型再基于结果继续推理或作答。本项目用 DeepSeek 的 function calling 声明了 `search_knowledge_base` 和 `query_order` 两个工具。

**Q14：什么是 ReAct？你的 Agent 循环怎么实现的？**
ReAct = Reasoning + Acting，让模型"边想边做"：推理该用什么工具 → 执行 → 观察结果 → 再推理，循环直到能作答。我的实现是一个 for 循环（上限 `agent_max_steps` 轮）：把 system + 历史 + 当前问题发给模型 → 若返回 `tool_calls` 就执行工具、把结果以 `tool` 角色追加进 messages、进入下一轮 → 若模型不再调工具，说明它准备作答，退出循环，最后流式输出答案。

**Q15：怎么防止模型无限调用工具？**
两层防护：① **硬上限** —— 循环最多 `agent_max_steps`（5）轮，超了强制退出，用已拿到的工具结果生成答案；② **提示词约束** —— system prompt 里明确「不需要查资料的问题直接回答」，减少无意义调用。此外工具自身要做参数校验（订单号为空直接返回提示，不查库）。

**Q16：工具执行的结果怎么让模型知道？**
把结果作为一条 `role="tool"` 的消息追加进 messages，并带上 `tool_call_id` 对应上模型那次调用。这是 OpenAI/DeepSeek 规定的协议：assistant 消息里的 `tool_calls` 有 id，`tool` 消息必须用同一个 id 回填，模型才知道"哪个调用的结果是这个"。整个 messages 数组就是这样一轮轮滚大的。

**Q17：Agent 版和之前的 RAG 版有什么本质区别？**
RAG 版是**写死的流水线**：不管问什么都走「改写 → 检索 → 生成」，检索是必经环节。Agent 版把「要不要检索、检索什么」的决定权交给模型：问「你好」直接回答（不检索），问订单就查订单表，问政策才检索知识库。区别在于**控制流由模型产生，而不是代码写死**——这才是 Agent 和普通 LLM 应用的分界线。代价是延迟变高（多一次模型调用），所以简单问题要尽量避免绕路。

**Q18：多轮对话的指代问题，Agent 版怎么解决的？**
旧版是硬编码一次 `_rewrite_query` 调用，改写后的问题固定拿去检索。Agent 版把对话历史直接放进 messages，由模型在生成 `tool_calls` 时自己决定检索用的 query —— 改写动作被吸收进了模型推理里，少一次独立的模型调用。同时我在工具描述里写明「query 必须是完整独立、不含指代的问题，例如『那多久到账』应改写为『退货退款多久到账』」，用工具描述引导模型产出高质量检索词。

**Q19：Agent 的中间步骤怎么让用户看到？**
后端在每次执行工具前，通过 SSE 推一条 `step` 事件（如「🛠 检索知识库：退货政策」）。前端 `handleEvent` 新增 `step` 分支，把标签追加到该条消息的 `steps` 数组上，渲染成气泡上方的灰色小标签。这样用户能直观看到"模型正在查什么"，既缓解等待焦虑，也是 Agent 可解释性的一部分。

**Q20：这个 Agent 还能怎么改进？**
① **订单查询加用户隔离** —— 目前按订单号全局查（类似游客查单），真实场景应校验订单归属，防止越权查到别人的订单；② **并行工具调用** —— 一轮里多个互不依赖的工具调用可并发执行；③ **流式工具决策** —— 现在 Agent 循环是非流式的，首字延迟偏高；④ **加可观测性** —— 记录每轮的 token 消耗、工具调用次数、耗时，便于评估与调优；⑤ **工具失败重试** —— 检索为空时可自动改写 query 重试一次。
