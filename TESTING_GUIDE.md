# 测试指南

## 已修复的问题

### 1. ✅ 管理员登录页面无法访问
**问题**: 访问 http://localhost:3001 看不到管理员登录界面
**原因**: AdminLogin.vue 中登录成功后跳转路径错误 (`/admin/dashboard` 应为 `/dashboard`)
**修复**: 
- 修改跳转路径为 `/dashboard`
- 修复 App.vue 中缺少的 `ref` 导入

### 2. ✅ 移除用户登录链接
**问题**: 管理员登录页面有"返回用户登录"链接
**修复**: 已删除该链接，管理员后台完全独立

### 3. ✅ 文档上传后无法根据内容回答
**问题**: 上传文档后，大模型看不到文档内容
**修复**: 在后端添加详细的调试日志，追踪文档读取过程

## 测试步骤

### 测试管理员登录 (端口 3001)

1. **启动管理员前端**
```bash
cd /Users/hsk/Desktop/Graduation\ Project/law-rag-assistant
./start_admin_frontend.sh
```

2. **访问管理员登录页**
- 打开浏览器: http://localhost:3001
- 应该看到管理员登录界面（📊 图标）
- 没有"返回用户登录"链接

3. **登录管理员账号**
- 输入管理员用户名和密码
- 点击"登录"
- 应该跳转到 `/dashboard` 显示统计数据

4. **检查浏览器控制台**
打开开发者工具 (F12)，查看 Console：
- 应该看到 `AdminDashboard mounted`
- 应该看到 `Fetching stats...`
- 应该看到 `Token: xxx`
- 应该看到 `Stats loaded: {...}`

如果看到错误，记录错误信息。

### 测试文档上传 (端口 3000)

1. **启动用户前端**
```bash
./start_user_frontend.sh
```

2. **登录并上传文档**
- 访问 http://localhost:3000
- 登录用户账号
- 点击输入框左侧的 ➕ 按钮
- 上传一个包含法律内容的 .txt 文件

3. **查看前端控制台**
应该看到类似输出：
```
Uploading file: xxx.txt
Upload result: { id: 123, ... }
Document ID set to: 123
```

4. **提问并查看日志**
- 输入问题："该怎么办"或其他问题
- 点击发送

**前端控制台应该显示**：
```
[ChatStore] sendMessage called with: { question: "该怎么办", documentId: 123 }
[ChatStore] Document ID provided, checking if question needs enhancement
[ChatStore] Question enhanced to: 根据上传的法律文件内容，该怎么办
[ChatStore] Calling chatStream with: { enhancedQuestion: "...", conversationId: null, documentId: 123 }
[API] chatStream request: { message: "...", conversation_id: null, use_document: 123 }
[API] chatStream response status: 200
[API] chatStream chunk: { token: "..." }
```

5. **查看后端日志**
```bash
tail -f /Users/hsk/Desktop/Graduation\ Project/law-rag-assistant/backend.log
```

**后端应该显示**：
```
📄 [流式] 用户请求使用文档 ID: 123
✅ [流式] 找到文档: xxx.txt, 路径: ./uploads/1/xxx.txt
✅ [流式] 文档内容读取成功: 1234 字符
```

## 常见问题排查

### 问题 1: 管理员登录后仍看不到数据
**检查项**：
1. 后端是否正常运行？访问 http://localhost:8000/docs
2. 管理员 token 是否有效？查看浏览器控制台
3. `/api/admin/stats` 接口是否返回数据？

### 问题 2: 文档上传后大模型仍然拒绝回答
**检查项**：
1. 文档是否上传成功？控制台是否显示 document ID？
2. 后端是否收到 `use_document` 参数？查看后端日志
3. 文档内容是否读取成功？后端日志是否显示"文档内容读取成功"？
4. 问题是否被增强？前端控制台是否显示"Question enhanced to"？

### 问题 3: 前端显示空白页
**检查项**：
1. npm run dev 是否成功启动？
2. 浏览器控制台是否有 JavaScript 错误？
3. 路由配置是否正确？

## 下一步优化

如果测试发现问题：
1. 记录所有控制台输出
2. 记录后端日志
3. 提供具体的错误信息

根据日志我们可以精确定位问题所在！
