# Vue 3 前端

基于 Vue 3 + Element Plus 的法律AI助手前端。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 快速的前端构建工具
- **Element Plus** - Vue 3 组件库
- **Pinia** - Vue 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **Markdown-it** - Markdown 渲染
- **Sass** - CSS 预处理器

## 项目结构

```
frontend-vue/
├── src/
│   ├── api/           # API 接口
│   ├── router/        # 路由配置
│   ├── stores/        # Pinia 状态管理
│   ├── styles/        # 全局样式
│   ├── views/         # 页面组件
│   ├── App.vue        # 根组件
│   └── main.js        # 入口文件
├── index.html         # HTML 模板
├── package.json       # 项目配置
└── vite.config.js     # Vite 配置
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend-vue
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

或使用启动脚本：

```bash
./start_vue_frontend.sh
```

### 3. 构建生产版本

```bash
npm run build
```

## 功能特性

- ✅ 暗色主题，简洁优雅
- ✅ 登录/注册
- ✅ 智能法律问答
- ✅ 对话历史管理
- ✅ 收藏夹功能
- ✅ 文件上传
- ✅ Markdown 渲染
- ✅ 响应式设计
- ✅ 丝滑的动画效果

## 开发说明

- 前端运行在 `http://localhost:3000`
- 后端 API 代理到 `http://localhost:8000/api`
- 确保后端服务已启动

## 注意事项

- 需要 Node.js 18+ 版本
- 后端服务必须先启动
