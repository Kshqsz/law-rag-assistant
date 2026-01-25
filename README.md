<div align="center">

# ⚖️ 法律 AI 助手

基于 RAG（检索增强生成）的智能法律咨询系统

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 项目简介

法律 AI 助手是一个基于检索增强生成（RAG）技术的智能法律咨询系统，能够：

- 🤖 基于中国法律法规知识库提供专业法律咨询
- 📚 结合向量数据库检索相关法律条文
- 🌐 补充网络搜索最新法律资讯
- 📄 支持用户上传文档进行针对性分析
- 💬 多轮对话，理解上下文
- ⭐ 收藏重要问答，导出 PDF 报告

---

## 🎯 核心特性

### 🔥 最新更新

#### 2026-01-25 更新

- ✅ **深色/浅色主题切换**：用户端新增主题切换功能，右上角一键切换
  - 🌙 深色模式：护眼舒适，适合夜间使用
  - ☀️ 浅色模式：清新明亮，适合白天使用
  - 💾 自动保存：主题偏好持久化存储，刷新页面自动恢复
  - 🎨 流畅过渡：基于 CSS 变量实现主题无缝切换

#### 2026-01-18 更新

##### 1. 前端架构重构

- ✅ **Vue3 现代化改造**：采用 Vue 3.4 + Vite 5 + Element Plus 重写前端
- ✅ **双前端分离**：用户端（3000）和管理员端（3001）独立运行
- ✅ **废弃 Streamlit**：移除旧的 Streamlit 前端，全面拥抱 Vue3
- ✅ **项目结构优化**：重新组织文件目录，归档废弃代码

##### 2. 功能增强

- ✅ **流式输出**：实时显示 AI 回答，优化用户体验
- ✅ **Markdown 渲染**：支持富文本格式显示，代码高亮
- ✅ **PDF 导出**：使用 html2pdf.js 支持中文导出
- ✅ **文档上传优化**：智能识别宽泛问题并增强提示
- ✅ **历史对话加载**：切换对话自动加载历史消息和网络来源
- ✅ **管理员统计**：新增问题增长趋势图和数据可视化

##### 3. 智能优化

- ✅ **法律相关性判断**：考虑历史上下文，拒绝无关问题
- ✅ **文档增强检索**：结合上传文档内容优化法律条文检索
- ✅ **HTML 标签禁止**：强制大模型使用标准 Markdown 格式
- ✅ **问题重写**：自动将代词问题改写为完整表述

### 🎨 用户端功能

- **智能对话**：多轮对话，理解上下文
- **法律检索**：自动检索相关法律条文
- **网络搜索**：补充最新法律资讯（DuckDuckGo）
- **文档上传**：支持 TXT/MD/PDF 文档分析
- **收藏管理**：保存重要问答
- **对话管理**：创建、删除、导出对话
- **实时流式**：逐字显示 AI 回答
- **主题切换**：深色/浅色模式一键切换，自动保存偏好

### 🛡️ 管理员端功能

- **数据统计**：用户数、对话数、消息数
- **趋势分析**：用户增长、问题增长趋势图
- **高频问题**：Top 10 热门问题统计
- **分类统计**：问题类型分布饼图
- **可视化**：基于 ECharts 的数据大屏

---

## 🏗️ 技术架构

后端技术栈

- **框架**：FastAPI（高性能异步 Web 框架）
- **数据库**：SQLite（轻量级关系数据库）
- **向量库**：ChromaDB（向量相似度检索）
- **LLM**：阿里云 DashScope（Qwen 系列模型）
- **RAG 引擎**：LangChain（检索增强生成框架）
- **Embedding**：DashScope text-embedding-v2
- **网络搜索**：DuckDuckGo（支持代理）

### 前端技术栈

- **框架**：Vue 3.4（Composition API）
- **构建工具**：Vite 5
- **UI 库**：Element Plus 2.4
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **HTTP 客户端**：Axios + Fetch（SSE）
- **图表**：ECharts 5
- **Markdown**：markdown-it
- **PDF 导出**：html2pdf.js

### RAG 工作流程

```
用户问题
    ↓
法律相关性判断 ← 历史上下文
    ↓
问题重写（如有代词）
    ↓
向量检索（ChromaDB）
    ↓
网络搜索（DuckDuckGo）
    ↓
文档增强（如有上传）
    ↓
上下文组装
    ↓
LLM 生成回答
    ↓
流式输出 + 保存数据库
```

### RAG 技术详解

**RAG（检索增强生成）的核心流程：**

1. **法律条文预处理**：法律条文被提前拆分成小段，存储到向量数据库
2. **向量化**：Embedding 模型把这些段落以及用户的问题都转成向量
3. **语义检索**：向量数据库根据"语义相似度"找到最相关的法律条文段落（可选：重排序模型再对这些段落进行排序，挑最最相关的）
4. **上下文注入**：这些段落以文本的形式放进 LLM
5. **生成回答**：LLM 根据 **用户问题 + 检索到的法律条文** 生成最终回答（相当于"开卷考试"）

**关于 Embedding 的两点补充：**

1. Embedding 看起来有理解能力，但这只是表面现象——它实际上就是一个**较为精准的向量转换器**
2. Embedding 就像一个干翻译的，把中文问题和法律条文都翻译成"向量语言"（高维数值向量）；用户输入问题后，由**向量数据库使用内部算法**找到最为相近的条文，然后让 LLM 在开卷考试的情况下回答问题

---

## 📁 项目结构

```
law-rag-assistant/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口
│   ├── auth.py                 # JWT 认证
│   ├── database.py             # 数据库模型
│   ├── law_service.py          # 法律问答服务
│   └── routers/                # API 路由
├── frontend-user/              # Vue3 用户前端
│   └── src/
│       ├── api/                # API 封装
│       ├── stores/             # Pinia 状态
│       └── views/              # 页面组件
├── frontend-admin/             # Vue3 管理员前端
│   └── src/
│       └── views/
│           └── AdminDashboard.vue  # 数据统计大屏
├── law_ai/                     # RAG 核心模块
│   ├── chain.py                # LangChain 链
│   ├── prompt.py               # 提示词模板
│   ├── retriever.py            # 检索器
│   └── utils.py                # 工具函数
├── Law-Book/                   # 法律知识库（Markdown）
│   ├── 1-宪法/
│   ├── 2-宪法相关法/
│   ├── 3-民法典/
│   └── ...
├── scripts/                    # 启动脚本
│   ├── start.sh                # 统一启动
│   ├── start_backend.sh
│   ├── start_user_frontend.sh
│   └── start_admin_frontend.sh
├── tests/                      # 测试文件
├── docs/                       # 项目文档
├── _archive/                   # 归档（废弃代码）
│   ├── frontend-streamlit/     # 旧 Streamlit 前端
│   └── frontend-vue-old/       # 旧 Vue 前端
└── config.py                   # 项目配置
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- 阿里云 DashScope API Key

### 1. 克隆项目

```bash
git clone <repository-url>
cd law-rag-assistant
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# LLM 配置
OPENAI_API_KEY=sk-你的阿里云DashScope-API-Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-max

# Embedding 配置
EMBEDDING_MODEL=text-embedding-v2

# 网络搜索代理（可选）
WEB_PROXY=http://127.0.0.1:7890
```

### 3. 安装依赖

#### 后端依赖

```bash
python -m venv venv311
source venv311/bin/activate  # Windows: venv311\Scripts\activate
pip install -r requirements.txt
```

#### 前端依赖

```bash
# 用户前端
cd frontend-user
npm install

# 管理员前端
cd ../frontend-admin
npm install
```

### 4. 初始化数据库

```bash
# 初始化管理员账户
python init_admin.py
```

### 5. 启动服务

#### 方式一：统一启动（推荐）

```bash
./scripts/start.sh
```

同时启动后端、用户前端和管理员前端。

#### 方式二：分别启动

```bash
# 终端 1：启动后端
./scripts/start_backend.sh

# 终端 2：启动用户前端
./scripts/start_user_frontend.sh

# 终端 3：启动管理员前端
./scripts/start_admin_frontend.sh
```

### 6. 访问服务

| 服务       | 地址                       | 说明          |
| ---------- | -------------------------- | ------------- |
| 后端 API   | http://localhost:8000      | FastAPI 服务  |
| API 文档   | http://localhost:8000/docs | Swagger UI    |
| 用户前端   | http://localhost:3000      | Vue3 用户界面 |
| 管理员前端 | http://localhost:3001      | Vue3 管理后台 |

**默认管理员账户**：

- 用户名：`admin`
- 密码：`admin123`

---

## 📝 使用说明

### 用户端

1. **注册/登录**：创建账户或使用现有账户登录
2. **开始对话**：直接输入法律相关问题
3. **上传文档**：点击 ➕ 上传文档进行针对性分析
4. **查看依据**：展开「法律依据」和「网络来源」查看详情
5. **收藏问答**：点击 ⭐ 收藏重要对话
6. **导出 PDF**：在对话列表中选择「导出 PDF」

### 管理员端

1. **登录**：使用管理员账户登录
2. **查看统计**：系统概览、用户数、对话数、消息数
3. **趋势分析**：用户增长和问题增长趋势图
4. **热点分析**：高频问题 Top 10 和分类统计

---

## 🔧 配置说明

### config.py 配置项

```python
# 向量库配置
LAW_VS_COLLECTION_NAME = "law_vector_store"
LAW_VS_SEARCH_K = 30  # 法律检索数量

# 网络搜索配置
WEB_VS_SEARCH_K = 5   # 网页检索数量
WEB_PROXY = "http://127.0.0.1:7890"  # 代理地址
```

### Prompt 优化

所有提示词在 `law_ai/prompt.py` 中定义，可根据需求调整：

- `LAW_PROMPT`：基础法律问答提示词
- `LAW_PROMPT_WITH_HISTORY`：带历史对话的提示词
- `CHECK_LAW_PROMPT`：法律相关性判断提示词
- `REWRITE_QUESTION_PROMPT`：问题重写提示词

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 单独测试
python tests/test_law_related_check.py
python tests/test_document_qa.py
```

---

## 📚 核心功能实现

### 1. 文档上传增强检索

上传文档后，系统会：

1. 提取文档前 300 字符作为上下文
2. 将问题与文档内容结合形成增强检索问题
3. 同时检索向量库和网络资源
4. 在 prompt 中优先展示文档内容

**代码位置**：`law_ai/chain.py` - `enhance_search_with_document`

### 2. 法律相关性智能判断

系统会判断问题是否与法律相关：

- 直接提到法律概念 → 回答
- 宽泛问题（如"这两者有什么区别"）→ 检查历史上下文
- 历史中有法律讨论 → 回答（延续讨论）
- 历史为空或无关 → 拒绝回答

**代码位置**：`backend/law_service.py` - `is_law_related`

### 3. 流式输出

使用 SSE（Server-Sent Events）实现实时流式输出：

- 后端使用 `StreamingResponse` 和异步生成器
- 前端使用 Fetch API 读取流
- 逐 token 显示，优化用户体验

**代码位置**：

- 后端：`backend/routers/chat.py` - `/stream`
- 前端：`frontend-user/src/stores/chat.js` - `sendMessage`

### 4. 历史对话加载

切换对话时自动加载历史消息：

- 监听 `currentConversationId` 变化
- 调用 API 获取历史消息
- 正确映射 `web_context` → `web_results`
- 显示法律依据和网络来源

**代码位置**：`frontend-user/src/views/Chat.vue` - `watch` 和 `loadConversationMessages`

---

## 🐛 已知问题与解决

### 问题 1：大模型输出 HTML 标签

**现象**：回答中出现 `<br>`、`<p>` 等 HTML 标签

**解决**：强化 prompt 约束，要求使用标准 Markdown 格式

### 问题 2：历史对话中看不到网络来源

**现象**：首次对话能看到网络来源，切换后消失

**解决**：添加历史消息加载逻辑，正确映射字段名

### 问题 3：收藏功能报错

**现象**：`NOT NULL constraint failed: favorites.message_id`

**解决**：修改数据库表结构，允许 `message_id` 为 NULL

### 问题 4：PDF 导出乱码

**现象**：导出的 PDF 中文显示为方块

**解决**：从 jsPDF 切换到 html2pdf.js，支持中文渲染

---

## 📊 性能优化

- **向量检索**：使用 ChromaDB 持久化，避免重复加载
- **批量处理**：异步并发处理多个检索请求
- **缓存机制**：LangChain 内置缓存减少 API 调用
- **流式输出**：边生成边显示，降低首屏时间
- **前端优化**：按需加载、路由懒加载、打包优化

---

## 🛠️ 开发者指南

### 添加新的法律分类

1. 在 `Law-Book/` 下创建新文件夹
2. 添加 Markdown 格式的法律文件
3. 重新运行向量化脚本（如需要）

### 自定义 Prompt

编辑 `law_ai/prompt.py`，修改 `law_prompt_template` 或其他模板。

### 添加新的 API 路由

在 `backend/routers/` 下创建新文件，定义路由并在 `main.py` 中注册。

### 前端组件开发

- 用户端：`frontend-user/src/views/`
- 管理员端：`frontend-admin/src/views/`
- 共享组件：使用 Element Plus 组件库

---

## 📖 更新日志

### 2026-01-18 - 重大重构版本

#### 前端架构

- ✅ Vue3 全面重写，废弃 Streamlit
- ✅ 用户端和管理员端分离
- ✅ 流式输出、Markdown 渲染、PDF 导出
- ✅ 历史对话加载、收藏功能优化

#### 后端优化

- ✅ 文档上传增强检索
- ✅ 法律相关性智能判断
- ✅ HTML 标签过滤
- ✅ 问题重写优化

#### 项目结构

- ✅ 重新组织目录结构
- ✅ 归档废弃代码到 `_archive/`
- ✅ 脚本移至 `scripts/`
- ✅ 文档移至 `docs/`
- ✅ 测试移至 `tests/`

### 2025-12-09 - 网络搜索修复

- ✅ 修复 DuckDuckGo 搜索
- ✅ 添加代理支持
- ✅ 优化搜索稳定性

### 2025-12-06 - 代码重构

- ✅ 优化 RAG 核心模块
- ✅ 改进文档加载逻辑

### 2025-12-05 - 初始适配

- ✅ 从 OpenAI 迁移到阿里云 DashScope
- ✅ 自定义 Embedding 实现

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 致谢

- **原始项目**：基于开源法律 RAG 项目改进
- **LLM 提供商**：阿里云 DashScope（Qwen 系列）
- **向量数据库**：ChromaDB
- **RAG 框架**：LangChain
- **前端框架**：Vue.js、Element Plus

---

## 📮 联系方式

- **作者**：Kshqsz
- **项目**：Law RAG Assistant

---

<div align="center">

Made with ❤️ by Kshqsz

⭐ 如果这个项目对你有帮助，请给一个 Star！

</div>
