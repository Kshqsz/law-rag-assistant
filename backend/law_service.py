# coding: utf-8
"""
法律问答服务模块：封装 RAG 链调用逻辑
"""
import sys
import os
import asyncio
from typing import Optional, Tuple, AsyncGenerator
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config import config
from law_ai.chain import get_law_chain, get_check_law_chain
from law_ai.callback import OutCallbackHandler
from law_ai.logger import app_logger


def print_separator(title: str = ""):
    """打印分隔符"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("=" * 60)


class LawQAService:
    """法律问答服务"""
    
    def __init__(self):
        self._check_chain = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            print_separator("法律问答服务初始化")
            app_logger.info("🚀 初始化法律问答服务...")
            self._check_chain = get_check_law_chain(config)
            self._initialized = True
            app_logger.info("✅ 法律问答服务初始化完成")
            print_separator()
    
    def is_law_related(self, question: str) -> bool:
        """检查问题是否与法律相关"""
        self._ensure_initialized()
        try:
            print(f"\n🔍 [检查] 判断问题是否与法律相关...")
            result = self._check_chain.invoke({"question": question})
            status = "✓ 是法律相关问题" if result else "✗ 不是法律相关问题"
            print(f"   {status}")
            return result
        except Exception as e:
            app_logger.warning(f"法律相关性检查失败: {e}")
            return True  # 如果检查失败，默认认为相关
    
    async def ask_question(
        self, 
        question: str,
        use_document_content: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """
        异步提问并获取回答
        
        Args:
            question: 用户问题
            use_document_content: 可选的文档内容（用于基于上传文档的问答）
            
        Returns:
            Tuple[answer, law_context, web_context]
        """
        self._ensure_initialized()
        
        # 打印开始处理
        timestamp = datetime.now().strftime("%H:%M:%S")
        print_separator(f"开始处理问题 [{timestamp}]")
        print(f"📝 用户问题: {question[:100]}{'...' if len(question) > 100 else ''}")
        
        has_document = use_document_content is not None
        if has_document:
            print(f"📎 附带文档: {len(use_document_content)} 字符")
        
        # 检查是否与法律相关
        if not self.is_law_related(question):
            print("❌ 问题与法律无关，拒绝回答")
            print_separator("处理结束")
            return (
                "不好意思，我是法律AI助手，请提问和法律有关的问题。",
                "",
                ""
            )
        
        out_callback = OutCallbackHandler()
        # 如果有上传文档，则禁用网页搜索；否则启用网页搜索
        enable_web = not has_document
        chain = get_law_chain(config, out_callback=out_callback, enable_web_search=enable_web)
        
        try:
            print("\n🔄 开始 RAG 检索流程...")
            app_logger.info(f"⏳ 处理问题: {question[:50]}...")
            
            # 不要在 config 中重复传递 callback，因为已经在 get_law_chain 中设置了
            task = asyncio.create_task(
                chain.ainvoke({"question": question})
            )
            
            # 收集流式输出
            answer = ""
            async for new_token in out_callback.aiter():
                answer += new_token
            
            out_callback.done.clear()
            
            # 获取结果
            res = await task
            
            # 提取法律引用和网页引用
            law_context = res.get("law_context", "")
            web_context = res.get("web_context", "")
            
            # 如果 answer 为空，从 res 获取
            if not answer:
                answer = res.get("answer", "抱歉，无法生成回答。")
            
            # 打印完成信息
            print("\n" + "=" * 60)
            print("✅ 回答生成完成!")
            print(f"   答案长度: {len(answer)} 字符")
            print(f"   法律引用: {len(law_context)} 字符")
            print(f"   网页引用: {len(web_context)} 字符")
            print_separator("处理结束")
            
            app_logger.info("✅ 问题处理完成")
            
            return answer, law_context, web_context
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            print_separator("处理结束")
            app_logger.error(f"❌ 问答服务错误: {e}")
            return f"抱歉，处理您的问题时出现错误：{str(e)}", "", ""
    
    async def stream_answer(
        self, 
        question: str,
        use_document_content: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成回答
        
        Args:
            question: 用户问题
            use_document_content: 可选的文档内容
            
        Yields:
            生成的文本片段
        """
        self._ensure_initialized()
        
        # 检查是否与法律相关
        if not self.is_law_related(question):
            yield "不好意思，我是法律AI助手，请提问和法律有关的问题。"
            return
        
        has_document = use_document_content is not None
        out_callback = OutCallbackHandler()
        # 如果有上传文档，则禁用网页搜索；否则启用网页搜索
        enable_web = not has_document
        chain = get_law_chain(config, out_callback=out_callback, enable_web_search=enable_web)
        
        try:
            app_logger.info(f"⏳ 流式处理问题: {question[:50]}...")
            
            # 创建任务 - 不要在 config 中重复传递 callback
            task = asyncio.create_task(
                chain.ainvoke({"question": question})
            )
            
            # 流式输出答案部分
            async for new_token in out_callback.aiter():
                yield new_token
            
            out_callback.done.clear()
            
            # 获取最终结果（包含 law_context 和 web_context）
            res = await task
            law_context = res.get("law_context", "")
            web_context = res.get("web_context", "")
            
            # 返回最终的上下文信息（以字典形式）
            yield {
                "law_context": law_context,
                "web_context": web_context
            }
            
            app_logger.info("✅ 流式问题处理完成")
            
        except Exception as e:
            app_logger.error(f"❌ 流式问答服务错误: {e}")
            yield f"\n\n抱歉，处理您的问题时出现错误：{str(e)}"


# 全局服务实例
law_qa_service = LawQAService()
