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

回答格式要求（必须严格遵守）：
1. 使用标准 Markdown 格式
2. **绝对禁止**使用任何 HTML 标签，包括但不限于：<br>、<p>、<div>、<table>、<tr>、<td> 等
3. 表格请使用 Markdown 表格语法：| 列名 | 列名 | 和 --- 分隔线
4. 列表项内的换行使用分号或编号，不要使用 <br>
5. 换行请直接使用两个换行符
"""
LAW_PROMPT = PromptTemplate(
    template=law_prompt_template, input_variables=["law_context", "web_context", "question"]
)

# 支持历史对话的提示词模板
law_prompt_with_history_template = """你是一个专业的律师，请你结合以下内容回答问题。

{law_context}

{web_context}

{history}

当前问题: {question}

注意：
1. 如果当前问题涉及上下文（如"它"、"这个"、"那个"、"继续"等代词），请参考历史对话理解完整含义
2. 如果是全新的问题，请直接回答，不要受历史对话影响
3. 保持回答的专业性和准确性

回答格式要求（必须严格遵守）：
1. 使用标准 Markdown 格式
2. **绝对禁止**使用任何 HTML 标签，包括但不限于：<br>、<p>、<div>、<table>、<tr>、<td> 等
3. 表格请使用 Markdown 表格语法：| 列名 | 列名 | 和 --- 分隔线
4. 列表项内的换行使用分号或编号，不要使用 <br>
5. 换行请直接使用两个换行符
"""
LAW_PROMPT_WITH_HISTORY = PromptTemplate(
    template=law_prompt_with_history_template, 
    input_variables=["law_context", "web_context", "history", "question"]
)

check_law_prompt_template = """你是一个专业律师，请判断下面问题是否和法律相关，相关请回答YES，不相关请回答NO，不允许其它回答，不允许在答案中添加编造成分。

{history}

当前问题: {question}

判断规则：
1. 如果问题直接提到法律、法规、犯罪、权利、合同、诉讼等法律概念，回答YES
2. 如果问题包含代词或指代词（如"它"、"这个"、"那"、"这些"、"两者"、"这两者"、"二者"等）或宽泛问题（如"有什么区别"、"有什么关系"、"该怎么办"）：
   - **必须检查历史对话是否为空**
   - 如果历史对话为空或只有"历史对话："没有实际内容，**必须回答NO**
   - 如果历史对话中明确讨论了法律概念（如"故意杀人"、"过失杀人"、"合同"、"侵权"等），则认为当前问题在延续法律讨论，回答YES
   - 如果历史对话存在但不涉及法律，回答NO
3. 对于日常生活问题（如"今天天气怎么样"、"你叫什么名字"），直接回答NO

**特别注意**：如果问题很宽泛且历史对话为空，一定要回答NO！
"""

CHECK_LAW_PROMPT = PromptTemplate(
    template=check_law_prompt_template, input_variables=["history", "question"]
)

# 问题重写提示词（用于包含代词的问题）
rewrite_question_prompt_template = """你是一个专业的律师助手。用户的问题可能包含代词或指代词（如"它"、"这个"、"那"、"这两种"等），请根据历史对话将问题重写为更明确的版本。

历史对话：
{history}

当前问题：{question}

请直接输出重写后的问题，不要添加任何解释。如果问题已经足够明确，则原样输出。

重写后的问题："""

REWRITE_QUESTION_PROMPT = PromptTemplate(
    template=rewrite_question_prompt_template, input_variables=["history", "question"]
)

hypo_questions_prompt_template = """生成 5 个假设问题的列表，以下文档可用于回答这些问题:\n\n{context}"""

HYPO_QUESTION_PROMPT = PromptTemplate(
    template=hypo_questions_prompt_template, input_variables=["context"]
)


multi_query_prompt_template = """您是 AI 语言模型助手。您的任务是生成给定用户问题的3个不同版本，以从矢量数据库中检索相关文档。通过对用户问题生成多个视角，您的目标是帮助用户克服基于距离的相似性搜索的一些限制。提供这些用换行符分隔的替代问题，不要给出多余的回答。问题：{question}""" # noqa
MULTI_QUERY_PROMPT_TEMPLATE = PromptTemplate(
    template=multi_query_prompt_template, input_variables=["question"]
)

# 通俗总结提示词（用于生成简短通俗的总结回答）
# 使用场景：在 law_service.py 的 ask_question 中，可选地为用户生成通俗易懂的总结
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
