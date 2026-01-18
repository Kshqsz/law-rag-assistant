# coding: utf-8
"""
LLM 异步流式回调处理模块

功能说明：
- OutCallbackHandler: 继承 AsyncIteratorCallbackHandler，用于处理 LLM 的流式输出
  当 LLM 生成输出时，通过异步迭代器的方式逐步返回结果，实现实时的流式响应

使用示例：
    from langchain.chat_models import ChatOpenAI
    from law_ai.callback import OutCallbackHandler
    
    # 创建异步回调处理器
    callback_handler = OutCallbackHandler()
    
    # 在 LLM 初始化时使用
    llm = ChatOpenAI(
        model="qwen-max",
        streaming=True,
        callbacks=[callback_handler]
    )
    
    # LLM 生成的结果会通过 callback_handler 逐步输出
    result = llm.invoke("什么是民法典？")
"""
from typing import Any, Dict, List, Optional
from langchain.callbacks import AsyncIteratorCallbackHandler


class OutCallbackHandler(AsyncIteratorCallbackHandler):
    """扩展 AsyncIteratorCallbackHandler，实现缺失的回调方法"""
    
    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """聊天模型开始时的回调（空实现以避免 NotImplementedError）"""
        pass
