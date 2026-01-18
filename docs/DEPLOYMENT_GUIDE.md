# 法律AI助手 - 启动说明

## 已完成的修改

### 1. 流式输出功能 ✅
- 前端现在使用 `/api/chat/stream` 接口实现流式输出
- 大模型回答会逐字显示，而不是一次性出现
- 前端使用 Server-Sent Events (SSE) 接收流式数据

### 2. 文档上传问题修复 ✅
- 修改了法律相关性检查逻辑
- 当用户上传文档后，系统会跳过问题相关性检查
- 即使问题本身看起来不相关（如"该怎么办"），系统也会基于文档内容回答

### 3. 前端端口分离 ✅
现在有三个独立的前端项目：
- **frontend-vue**: 原始项目 (端口 3000)
- **frontend-user**: 用户端 (端口 3000) - 只包含聊天和收藏功能
- **frontend-admin**: 管理员端 (端口 3001) - 只包含管理员仪表盘

## 启动方式

### 启动后端 (必须)
```bash
cd /Users/hsk/Desktop/Graduation\ Project/law-rag-assistant
source venv311/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动用户前端 (端口 3000)
```bash
cd /Users/hsk/Desktop/Graduation\ Project/law-rag-assistant/frontend-user
npm run dev
```
访问: http://localhost:3000

### 启动管理员前端 (端口 3001)
```bash
cd /Users/hsk/Desktop/Graduation\ Project/law-rag-assistant/frontend-admin
npm run dev
```
访问: http://localhost:3001

### 或使用快捷脚本
```bash
# 启动用户前端
./start_user_frontend.sh

# 启动管理员前端  
./start_admin_frontend.sh
```

## 功能说明

### 用户端 (端口 3000)
- ✅ 用户注册/登录
- ✅ 法律问题咨询（流式输出）
- ✅ 文件上传并基于文件内容提问
- ✅ 对话历史管理
- ✅ 收藏功能
- ✅ PDF导出（在历史对话下拉菜单中）

### 管理员端 (端口 3001)
- ✅ 管理员登录
- ✅ 用户统计
- ✅ 问答统计
- ✅ 数据可视化图表

## 测试流程

1. **测试流式输出**:
   - 启动后端和用户前端
   - 登录用户账号
   - 提问法律问题
   - 观察回答是否逐字显示

2. **测试文档上传**:
   - 上传包含法律内容的文本文件
   - 提问简单问题如"该怎么办"
   - 系统应该基于文档内容回答，而不是拒绝

3. **测试管理员端**:
   - 访问 http://localhost:3001
   - 使用管理员账号登录
   - 查看统计数据和图表

## 注意事项

- 后端必须先启动
- 确保端口 3000、3001、8000 没有被占用
- 用户端和管理员端可以同时运行
- 建议使用 Chrome 或 Firefox 浏览器
