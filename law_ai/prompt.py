# coding: utf-8
"""
提示词模板模块

功能说明：
- LAW_PROMPT: 主要的法律问答提示词模板
  结合法律条文和网页信息来回答法律问题
  输入变量: law_context (法律条文), web_context (网页信息), question (用户问题)
  
- CHECK_LAW_PROMPT: 法律相关性检查提示词
  用于判断用户问题是否与法律相关 (仅回答 YES 或 NO)
  输入变量: question (用户问题)
  
- HYPO_QUESTION_PROMPT: 假设问题生成提示词
  根据文档内容生成可能的假设问题
  输入变量: context (文档内容)
  
- MULTI_QUERY_PROMPT_TEMPLATE: 多查询生成提示词
  根据用户问题生成 3 个不同视角的变体问题，用于向量检索
  输入变量: question (用户问题)

使用示例：
    from langchain.prompts import PromptTemplate
    from law_ai.prompt import LAW_PROMPT, CHECK_LAW_PROMPT
    from law_ai.utils import get_model
    
    # 示例 1: 使用 LAW_PROMPT 进行法律问答
    llm = get_model()
    
    law_context = \"\"\"相关法律：《中华人民共和国刑法》
    第二百三十二条 故意杀人的，处死刑。\"\"\"
    web_context = \"\"\"根据最高人民法院解释，故意杀人必须有杀人故意。\"\"\"
    question = "故意杀人应该怎么处罚？"
    
    # 格式化提示词
    prompt_input = LAW_PROMPT.format(
        law_context=law_context,
        web_context=web_context,
        question=question
    )
    print("格式化后的提示词：")
    print(prompt_input)
    # 输出:
    # 你是一个专业的律师，请你结合以下内容回答问题:
    # 相关法律：《中华人民共和国刑法》
    # 第二百三十二条 故意杀人的，处死刑。
    # 根据最高人民法院解释，故意杀人必须有杀人故意。
    # 问题: 故意杀人应该怎么处罚？
    
    # 示例 2: 使用 CHECK_LAW_PROMPT 检查问题是否与法律相关
    check_prompt = CHECK_LAW_PROMPT.format(question="什么是民法典？")
    print("检查提示词：")
    print(check_prompt)
    # 输出:
    # 你是一个专业律师，请判断下面问题是否和法律相关，相关请回答YES，不想关请回答NO
    # 问题: 什么是民法典？
"""
from langchain.prompts import PromptTemplate

law_prompt_template = """你是一个专业的律师，请你结合以下内容回答问题:
{law_context}

{web_context}

问题: {question}
"""
LAW_PROMPT = PromptTemplate(
    template=law_prompt_template, input_variables=["law_context", "web_context", "question"]
)

check_law_prompt_template = """你是一个专业律师，请判断下面问题是否和法律相关，相关请回答YES，不想关请回答NO，不允许其它回答，不允许在答案中添加编造成分。
问题: {question}
"""

CHECK_LAW_PROMPT = PromptTemplate(
    template=check_law_prompt_template, input_variables=["question"]
)

hypo_questions_prompt_template = """生成 5 个假设问题的列表，以下文档可用于回答这些问题:\n\n{context}"""

HYPO_QUESTION_PROMPT = PromptTemplate(
    template=hypo_questions_prompt_template, input_variables=["context"]
)


multi_query_prompt_template = """您是 AI 语言模型助手。您的任务是生成给定用户问题的3个不同版本，以从矢量数据库中检索相关文档。通过对用户问题生成多个视角，您的目标是帮助用户克服基于距离的相似性搜索的一些限制。提供这些用换行符分隔的替代问题，不要给出多余的回答。问题：{question}""" # noqa
MULTI_QUERY_PROMPT_TEMPLATE = PromptTemplate(
    template=multi_query_prompt_template, input_variables=["question"]
)

# 通俗总结提示词
summary_prompt_template = """你是一个专业且善于沟通的律师。现在你已经为用户提供了详细的法律依据和网络资料。

请基于以下内容，用通俗易懂的语言为用户总结回答：

法律依据：
{law_context}

网络资料：
{web_context}

用户问题：{question}

请注意：
1. 用简单明了的语言解释，避免过多法律术语
2. 突出重点和关键结论
3. 如果涉及具体数字（如罚款、刑期等），请明确指出
4. 长度控制在200字以内
5. 语气要亲切、专业

通俗总结："""

SUMMARY_PROMPT = PromptTemplate(
    template=summary_prompt_template, 
    input_variables=["law_context", "web_context", "question"]
)
