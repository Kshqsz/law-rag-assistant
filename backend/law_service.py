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
    
    def is_law_related(self, question: str, history: Optional[list] = None) -> bool:
        """检查问题是否与法律相关
        
        Args:
            question: 用户问题
            history: 历史对话，格式为 [{"role": "user", "content": "..."}]
        """
        self._ensure_initialized()
        try:
            print(f"\n🔍 [检查] 判断问题是否与法律相关...")
            
            # 如果有历史，格式化为简短文本供校验使用
            history_for_check = ""
            if history:
                history_for_check = "历史对话：\n"
                for msg in history[-4:]:  # 只用最近2轮对话
                    role_name = "用户" if msg["role"] == "user" else "律师"
                    history_for_check += f"{role_name}: {msg['content'][:100]}\n"
            
            result = self._check_chain.invoke({
                "history": history_for_check,
                "question": question
            })
            status = "✓ 是法律相关问题" if result else "✗ 不是法律相关问题"
            print(f"   {status}")
            return result
        except Exception as e:
            app_logger.warning(f"法律相关性检查失败: {e}")
            return True  # 如果检查失败，默认认为相关
    
    def _contains_pronoun(self, question: str) -> bool:
        """检查问题是否包含代词或指代词"""
        pronouns = ["它", "这个", "那个", "这", "那", "这些", "那些", "此", "该", 
                   "这种", "那种", "这两", "那两", "上述", "前面", "以上", "上面提到"]
        return any(pronoun in question for pronoun in pronouns)
    
    def _rewrite_question_with_history(self, question: str, history: list) -> str:
        """根据历史对话重写问题，使其更明确"""
        from law_ai.chain import get_check_law_chain
        from law_ai.prompt import REWRITE_QUESTION_PROMPT
        from law_ai.utils import get_model
        
        try:
            # 格式化历史对话
            history_text = ""
            for msg in history[-6:]:  # 使用最近3轮对话
                role_name = "用户" if msg["role"] == "user" else "律师"
                history_text += f"{role_name}: {msg['content'][:200]}\n\n"
            
            # 调用LLM重写问题
            model = get_model()
            rewrite_chain = REWRITE_QUESTION_PROMPT | model
            rewritten = rewrite_chain.invoke({
                "history": history_text,
                "question": question
            })
            
            # 提取重写后的文本
            if hasattr(rewritten, 'content'):
                return rewritten.content.strip()
            else:
                return str(rewritten).strip()
        except Exception as e:
            app_logger.warning(f"问题重写失败: {e}，使用原问题")
            return question
    
    async def ask_question(
        self, 
        question: str,
        use_document_content: Optional[str] = None,
        history: Optional[list] = None
    ) -> Tuple[str, str, str]:
        """
        异步提问并获取回答
        
        Args:
            question: 用户问题
            use_document_content: 可选的文档内容（用于基于上传文档的问答）
            history: 历史对话列表，格式为 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
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
        if not self.is_law_related(question, history):
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
            
            # 如果有历史对话且问题可能包含代词，先重写问题以提高检索准确度
            search_question = question
            if history and self._contains_pronoun(question):
                print("🔍 检测到代词，正在重写问题以提高检索准确度...")
                search_question = self._rewrite_question_with_history(question, history)
                print(f"📝 重写后的问题: {search_question[:100]}{'...' if len(search_question) > 100 else ''}")
            
            # 准备输入参数（检索使用重写后的问题，但回答仍使用原问题）
            chain_input = {"question": question, "search_question": search_question}
            
            # 如果有历史对话，添加到输入中
            if history:
                print(f"📜 包含历史对话: {len(history)} 条消息")
                chain_input["history"] = history
            
            # 不要在 config 中重复传递 callback，因为已经在 get_law_chain 中设置了
            task = asyncio.create_task(
                chain.ainvoke(chain_input)
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
        use_document_content: Optional[str] = None,
        history: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成回答
        
        Args:
            question: 用户问题
            use_document_content: 可选的文档内容
            history: 历史对话列表
            
        Yields:
            生成的文本片段
        """
        self._ensure_initialized()
        
        # 检查是否与法律相关
        if not self.is_law_related(question, history):
            yield "不好意思，我是法律AI助手，请提问和法律有关的问题。"
            return
        
        has_document = use_document_content is not None
        out_callback = OutCallbackHandler()
        # 如果有上传文档，则禁用网页搜索；否则启用网页搜索
        enable_web = not has_document
        chain = get_law_chain(config, out_callback=out_callback, enable_web_search=enable_web)
        
        try:
            app_logger.info(f"⏳ 流式处理问题: {question[:50]}...")
            
            # 如果有历史对话且问题可能包含代词，先重写问题以提高检索准确度
            search_question = question
            if history and self._contains_pronoun(question):
                search_question = self._rewrite_question_with_history(question, history)
                app_logger.info(f"📝 重写后的检索问题: {search_question[:50]}...")
            
            # 准备输入参数（检索使用重写后的问题，但回答仍使用原问题）
            chain_input = {"question": question, "search_question": search_question}
            if history:
                chain_input["history"] = history
            
            # 创建任务 - 不要在 config 中重复传递 callback
            task = asyncio.create_task(
                chain.ainvoke(chain_input)
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
