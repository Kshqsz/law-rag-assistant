# coding: utf-8
"""
法律 AI RAG 系统主模块

该包提供法律问答系统的核心功能，包括：
- 法律文档加载与处理（loader.py）
- 法律文本分割（splitter.py）
- 向量检索与网页搜索（retriever.py）
- RAG 链式处理（chain.py）
- 文档合并与格式化（combine.py）
- 模型与向量库管理（utils.py）
- 提示词模板（prompt.py）
- 日志输出（logger.py）
- 异步回调处理（callback.py）

用户通过 manager.py 的交互界面（Web UI 或 Shell）与系统交互，
系统会自动调用各个模块完成法律问题的检索与回答。
"""
