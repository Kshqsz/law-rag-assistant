# 法律 AI 助手使用指南

本指南基于当前项目结构编写，按实际使用顺序说明：先构建法律向量数据库，再启动后端与双前端，最后完成用户与管理员侧操作。

## 1. 环境准备

### 1.1 基础依赖

- Python 3.11+
- Node.js 18+
- npm

### 1.2 安装后端依赖

```bash
python -m venv venv311
source venv311/bin/activate
pip install -r requirements.txt
```

### 1.3 安装前端依赖

```bash
cd frontend-user && npm install
cd ../frontend-admin && npm install
cd ..
```

### 1.4 配置环境变量

项目根目录创建 `.env`（可参考 `.env.example`）：

```env
OPENAI_API_KEY="sk-你的DashScope密钥"
OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME="qwen-plus"

EMBEDDING_API_KEY="sk-你的DashScope密钥"
EMBEDDING_MODEL="text-embedding-v2"
EMBEDDING_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

SECRET_KEY="请替换为你自己的随机密钥"
```

## 2. 构建向量数据库（第一步）

法律问答依赖向量检索，首次部署或法律文书更新后，必须先构建/重建向量库。

### 2.1 增量构建（默认）

```bash
source venv311/bin/activate
python scripts/build_vector_db.py
```

适用场景：
- 仅新增部分法律文书
- 需要保留已有索引并增量更新

### 2.2 清空后重建（推荐用于大改动）

```bash
source venv311/bin/activate
python scripts/build_vector_db.py --clear
```

适用场景：
- 法律文书目录有大规模替换
- 需要避免旧索引残留

### 2.3 可选参数

```bash
python scripts/build_vector_db.py --clear --law-dir ./Law-Book --chunk-size 1000 --chunk-overlap 100
```

执行完成后，会输出新增/更新/跳过/删除数量，可据此判断索引是否成功刷新。

## 3. 启动系统

### 3.1 一键启动（推荐）

```bash
./scripts/start.sh
```

该脚本会自动：
- 启动后端 API（8000）
- 启动用户前端（3000）
- 启动管理员前端（3001）

### 3.2 手动分开启动（调试用）

终端 1：

```bash
source venv311/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

终端 2：

```bash
cd frontend-user
npm run dev
```

终端 3：

```bash
cd frontend-admin
npm run dev
```

## 4. 访问地址

| 服务 | 地址 | 说明 |
|---|---|---|
| 用户前端 | http://localhost:3000 | 注册、登录、法律问答、收藏、导出 |
| 管理员前端 | http://localhost:3001 | 统计看板、用户管理 |
| 后端 API | http://localhost:8000 | 主服务接口 |
| API 文档 | http://localhost:8000/api/docs | Swagger 文档 |

## 5. 初始化管理员账号（如尚未创建）

如果管理员账号不存在，可先调用初始化接口：

```bash
curl -X POST "http://localhost:8000/api/admin/create-admin?username=admin&password=admin123"
```

默认示例账号：
- 用户名：admin
- 密码：admin123

建议在正式环境创建后立即修改。

## 6. 用户侧使用流程

1. 打开用户前端，注册或登录账号。
2. 在聊天页输入法律问题发起问答。
3. 需要结合材料时，先上传文档再提问。
4. 对重要回答可点击收藏。
5. 在历史会话中可导出 PDF。

## 7. 管理员侧使用流程

1. 打开管理员前端登录管理员账号。
2. 查看系统概览、用户趋势、问题分类、Token 使用等统计。
3. 在用户管理中进行启用/禁用、重置密码等运维操作。

## 8. 常用维护命令

### 8.1 引用准确率分析

```bash
source venv311/bin/activate
python scripts/analyze_citation_accuracy.py
```

### 8.2 检索增强与直接回答对比评测

```bash
source venv311/bin/activate
python scripts/evaluate_rag_vs_base.py --dataset tests/ab_eval_dataset.sample.jsonl --output-dir evaluation_results --model-name qwen-plus --limit 0
```

## 9. 常见问题排查

### 9.1 提示“向量检索无结果”

- 确认是否已执行第 2 节向量库构建。
- 检查 `Law-Book` 目录是否有有效法律文书。

### 9.2 前端无法连接后端

- 确认后端是否运行在 8000 端口。
- 确认前端 Vite 代理目标仍是 `http://localhost:8000`。

### 9.3 DashScope 调用失败

- 检查 `.env` 中 API Key 和 Base URL 是否正确。
- 确认本机网络可访问 DashScope。

### 9.4 管理员登录后看不到统计

- 确认账号具有管理员权限。
- 可先调用管理员初始化接口重新设置管理员身份。

## 10. 推荐日常操作顺序

1. 更新法律文书（如有）
2. 运行向量库构建（增量或清空重建）
3. 启动后端与前端
4. 先做用户侧问答验证，再做管理员侧统计验证
5. 需要评估时运行引用准确率与对比评测脚本
